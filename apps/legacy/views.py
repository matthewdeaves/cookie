"""Views for legacy frontend."""

import logging
import re
from functools import wraps

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from apps.core.decorators import require_admin
from apps.core.models import AppSettings
from apps.core.utils import is_admin
from apps.profiles.models import Profile
from apps.profiles.validators import validate_registration
from apps.ai.models import AIPrompt

logger = logging.getLogger(__name__)
from apps.ai.services.openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeFavorite,
    RecipeViewHistory,
)


def require_profile(view_func):
    """Decorator to ensure a profile is selected and valid.

    Home mode:
    - Gets profile_id from session, validates it exists
    - Redirects to profile_selector if no session or profile missing

    Public mode:
    - Requires user to be authenticated
    - Uses request.user.profile
    - Redirects to login if not authenticated

    Adds the Profile instance to request.profile.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        settings = AppSettings.get()
        deployment_mode = settings.get_deployment_mode()

        if deployment_mode == "public":
            # Public mode: require authentication
            if not request.user.is_authenticated:
                return redirect("legacy:login")

            # Get user's profile
            if not hasattr(request.user, "profile"):
                # User exists but no profile - shouldn't happen, redirect to login
                return redirect("legacy:login")

            request.profile = request.user.profile
        else:
            # Home mode: use session
            profile_id = request.session.get("profile_id")
            if not profile_id:
                return redirect("legacy:profile_selector")

            try:
                request.profile = Profile.objects.get(id=profile_id)
            except Profile.DoesNotExist:
                del request.session["profile_id"]
                return redirect("legacy:profile_selector")

        return view_func(request, *args, **kwargs)

    return wrapper


def _is_ai_available() -> bool:
    """Check if AI features are available (key configured AND valid)."""
    settings = AppSettings.get()
    if not settings.openrouter_api_key:
        return False
    is_valid, _ = OpenRouterService.validate_key_cached()
    return is_valid


def profile_selector(request):
    """Profile selector screen.

    In public mode, redirect to login page (no profile selector).
    In home mode, show profile selector.
    """
    settings = AppSettings.get()

    # Public mode: redirect to login
    if settings.get_deployment_mode() == "public":
        # If already authenticated, go to home
        if request.user.is_authenticated:
            return redirect("legacy:home")
        return redirect("legacy:login")

    # Home mode: show profile selector
    profiles = list(Profile.objects.all().values("id", "name", "avatar_color", "theme", "unit_preference"))
    return render(
        request,
        "legacy/profile_selector.html",
        {
            "profiles": profiles,
        },
    )


def _get_client_ip(request):
    """Get client IP address from request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def _get_nav_context(request):
    """Get common navigation context for templates."""
    settings = AppSettings.get()
    return {
        "is_admin": is_admin(request.user),
        "is_public_mode": settings.get_deployment_mode() == "public",
    }


def login_view(request):
    """Login view for public mode."""
    settings = AppSettings.get()

    # If home mode, redirect to profile selector
    if settings.get_deployment_mode() == "home":
        return redirect("legacy:profile_selector")

    # If already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect("legacy:home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Successful login - django.contrib.auth.login regenerates session ID
            login(request, user)

            # Set profile_id in session for compatibility
            if hasattr(user, "profile"):
                request.session["profile_id"] = user.profile.id

            return redirect("legacy:home")
        else:
            # Failed login - use same error message for all failures (prevents username enumeration)
            logger.warning(f"Failed login attempt for username={username} ip={_get_client_ip(request)}")
            error = "Invalid username or password"

    return render(
        request,
        "legacy/login.html",
        {
            "error": error,
            "instance_name": settings.get_instance_name(),
            "allow_registration": settings.get_allow_registration(),
        },
    )


def register_view(request):
    """Registration view for public mode."""
    settings = AppSettings.get()

    # If home mode, redirect to profile selector
    if settings.get_deployment_mode() == "home":
        return redirect("legacy:profile_selector")

    # If registration disabled, redirect to login
    if not settings.get_allow_registration():
        return redirect("legacy:login")

    # If already authenticated, redirect to home
    if request.user.is_authenticated:
        return redirect("legacy:home")

    error = None

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        password_confirm = request.POST.get("password_confirm", "")
        avatar_color = request.POST.get("avatar_color", "#6366f1")

        # Validation using shared validators
        validation = validate_registration(username, password, password_confirm)
        if not validation.is_valid:
            error = validation.error
        else:
            # Create user and profile
            user = User.objects.create_user(username=username, password=password)
            Profile.objects.create(
                user=user,
                name=username,
                avatar_color=avatar_color,
            )

            # Log in the new user
            login(request, user)
            request.session["profile_id"] = user.profile.id

            return redirect("legacy:home")

    return render(
        request,
        "legacy/register.html",
        {
            "error": error,
            "instance_name": settings.get_instance_name(),
        },
    )


def logout_view(request):
    """Logout view."""
    settings = AppSettings.get()
    deployment_mode = settings.get_deployment_mode()

    # Clear Django auth
    logout(request)

    # Clear session profile_id
    if "profile_id" in request.session:
        del request.session["profile_id"]

    # Redirect based on mode
    if deployment_mode == "public":
        return redirect("legacy:login")
    else:
        return redirect("legacy:profile_selector")


@require_profile
def home(request):
    """Home screen."""
    profile = request.profile

    # Get favorites for this profile
    favorites_qs = RecipeFavorite.objects.filter(profile=profile).select_related("recipe").order_by("-created_at")
    favorites_count = favorites_qs.count()
    favorites = favorites_qs[:12]

    # Get recently viewed for this profile
    history_qs = RecipeViewHistory.objects.filter(profile=profile).select_related("recipe").order_by("-viewed_at")
    history = history_qs[:6]

    # Get total recipe count (for "My Recipes" link)
    recipes_count = Recipe.objects.filter(profile=profile).count()

    # Build favorite recipe IDs set for checking
    favorite_recipe_ids = set(f.recipe_id for f in favorites)

    # Check if AI features are available
    ai_available = _is_ai_available()

    return render(
        request,
        "legacy/home.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "favorites": favorites,
            "favorites_count": favorites_count,
            "history": history,
            "recipes_count": recipes_count,
            "favorite_recipe_ids": favorite_recipe_ids,
            "ai_available": ai_available,
            **_get_nav_context(request),
        },
    )


@require_profile
def search(request):
    """Search results screen."""
    profile = request.profile

    query = request.GET.get("q", "")
    # Detect if query is a URL
    is_url = query.strip().startswith("http://") or query.strip().startswith("https://")

    return render(
        request,
        "legacy/search.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "query": query,
            "is_url": is_url,
            **_get_nav_context(request),
        },
    )


@require_profile
def recipe_detail(request, recipe_id):
    """Recipe detail screen."""
    profile = request.profile

    # Get the recipe (must belong to this profile)
    recipe = get_object_or_404(Recipe, id=recipe_id, profile=profile)

    # Record view history
    RecipeViewHistory.objects.update_or_create(
        profile=profile,
        recipe=recipe,
        defaults={},  # Just update viewed_at (auto_now)
    )

    # Check if recipe is favorited
    is_favorite = RecipeFavorite.objects.filter(
        profile=profile,
        recipe=recipe,
    ).exists()

    # Get user's collections for the "add to collection" feature
    collections = RecipeCollection.objects.filter(profile=profile)

    # Check if AI features are available
    ai_available = _is_ai_available()

    # Prepare ingredient groups or flat list
    has_ingredient_groups = bool(recipe.ingredient_groups)

    # Prepare instructions
    instructions = recipe.instructions
    if not instructions and recipe.instructions_text:
        instructions = [s.strip() for s in recipe.instructions_text.split("\n") if s.strip()]

    # Build linked recipes for navigation
    linked_recipes = []
    if recipe.remixed_from_id:
        # This is a remix - link to original
        original = recipe.remixed_from
        if original:
            linked_recipes.append(
                {
                    "id": original.id,
                    "title": original.title,
                    "relationship": "original",
                }
            )
            # Also find sibling remixes (other remixes of the same original)
            siblings = Recipe.objects.filter(
                remixed_from=original,
                profile=profile,
            ).exclude(id=recipe.id)[:5]
            for sibling in siblings:
                linked_recipes.append(
                    {
                        "id": sibling.id,
                        "title": sibling.title,
                        "relationship": "sibling",
                    }
                )
    else:
        # This is an original - find its remixes
        remixes = Recipe.objects.filter(
            remixed_from=recipe,
            profile=profile,
        )[:5]
        for remix in remixes:
            linked_recipes.append(
                {
                    "id": remix.id,
                    "title": remix.title,
                    "relationship": "remix",
                }
            )

    return render(
        request,
        "legacy/recipe_detail.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "recipe": recipe,
            "is_favorite": is_favorite,
            "collections": collections,
            "ai_available": ai_available,
            "has_ingredient_groups": has_ingredient_groups,
            "instructions": instructions,
            "linked_recipes": linked_recipes,
            **_get_nav_context(request),
        },
    )


@require_profile
def play_mode(request, recipe_id):
    """Play mode / cooking mode screen."""
    profile = request.profile

    # Get the recipe (must belong to this profile)
    recipe = get_object_or_404(Recipe, id=recipe_id, profile=profile)

    # Check if AI features are available
    ai_available = _is_ai_available()

    # Prepare instructions
    instructions = recipe.instructions
    if not instructions and recipe.instructions_text:
        instructions = [s.strip() for s in recipe.instructions_text.split("\n") if s.strip()]

    return render(
        request,
        "legacy/play_mode.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "recipe": recipe,
            "instructions": instructions,
            "instructions_json": instructions,  # For JavaScript
            "ai_available": ai_available,
            **_get_nav_context(request),
        },
    )


@require_profile
def all_recipes(request):
    """My Recipes screen - shows all recipes owned by this profile."""
    profile = request.profile

    # Get all recipes for this profile (imports + remixes)
    recipes = Recipe.objects.filter(profile=profile).order_by("-scraped_at")

    # Build set of favorite recipe IDs for display
    favorite_recipe_ids = set(RecipeFavorite.objects.filter(profile=profile).values_list("recipe_id", flat=True))

    return render(
        request,
        "legacy/all_recipes.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "recipes": recipes,
            "favorite_recipe_ids": favorite_recipe_ids,
            **_get_nav_context(request),
        },
    )


@require_profile
def favorites(request):
    """Favorites screen - shows all favorited recipes."""
    profile = request.profile

    # Get all favorites for this profile
    favorites = RecipeFavorite.objects.filter(profile=profile).select_related("recipe").order_by("-created_at")

    return render(
        request,
        "legacy/favorites.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "favorites": favorites,
            **_get_nav_context(request),
        },
    )


@require_profile
def collections(request):
    """Collections list screen."""
    profile = request.profile

    # Get all collections for this profile
    collections = (
        RecipeCollection.objects.filter(profile=profile).prefetch_related("items__recipe").order_by("-updated_at")
    )

    return render(
        request,
        "legacy/collections.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "collections": collections,
            **_get_nav_context(request),
        },
    )


@require_profile
def collection_detail(request, collection_id):
    """Collection detail screen - shows recipes in a collection."""
    profile = request.profile

    # Get the collection (must belong to this profile)
    collection = get_object_or_404(RecipeCollection, id=collection_id, profile=profile)

    # Get all items in this collection
    items = collection.items.select_related("recipe").order_by("order", "-added_at")

    # Build set of favorite recipe IDs for display
    favorite_recipe_ids = set(RecipeFavorite.objects.filter(profile=profile).values_list("recipe_id", flat=True))

    return render(
        request,
        "legacy/collection_detail.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "collection": collection,
            "items": items,
            "favorite_recipe_ids": favorite_recipe_ids,
            **_get_nav_context(request),
        },
    )


@require_admin
@require_profile
def settings(request):
    """Settings screen - AI prompts and sources configuration.

    Protected by @require_admin - only accessible to admin users.
    In home mode, all users are admin. In public mode, only
    the user matching COOKIE_ADMIN_USERNAME is admin.
    """
    profile = request.profile

    # Get app settings
    app_settings = AppSettings.get()

    # Check if AI features are available
    ai_available = _is_ai_available()

    # Get all AI prompts
    prompts = list(AIPrompt.objects.all().order_by("name"))

    # Get available models from OpenRouter
    try:
        service = OpenRouterService()
        models = service.get_available_models()
    except (AIUnavailableError, AIResponseError):
        models = []

    return render(
        request,
        "legacy/settings.html",
        {
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "avatar_color": profile.avatar_color,
            },
            "current_profile_id": profile.id,
            "ai_available": ai_available,
            "default_model": app_settings.default_ai_model,
            "prompts": prompts,
            "models": models,
            **_get_nav_context(request),
        },
    )
