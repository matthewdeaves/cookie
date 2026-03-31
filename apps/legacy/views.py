"""Views for legacy frontend."""

from functools import wraps

from django.conf import settings as django_settings
from django.shortcuts import render, redirect, get_object_or_404

from apps.core.models import AppSettings
from apps.profiles.models import Profile
from apps.ai.models import AIPrompt
from apps.ai.services.openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeFavorite,
    RecipeViewHistory,
)


def require_profile(view_func):
    """Decorator to ensure a profile is selected and valid.

    In passkey mode, redirects to device pairing instead of profile_selector.
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        profile_id = request.session.get("profile_id")
        if django_settings.AUTH_MODE == "passkey":
            redirect_target = "legacy:device_pair"
        else:
            redirect_target = "legacy:profile_selector"

        if not profile_id:
            return redirect(redirect_target)

        try:
            request.profile = Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            request.session.pop("profile_id", None)
            return redirect(redirect_target)

        # In passkey mode, check that profile has a linked active user
        if django_settings.AUTH_MODE == "passkey":
            if not request.profile.user or not request.profile.user.is_active:
                request.session.pop("profile_id", None)
                return redirect(redirect_target)
            request.is_admin = request.profile.user.is_staff
        else:
            request.is_admin = True

        return view_func(request, *args, **kwargs)

    return wrapper


def require_admin(view_func):
    """Decorator for admin-only legacy views (passkey mode)."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if django_settings.AUTH_MODE == "passkey" and not getattr(request, "is_admin", False):
            return redirect("legacy:home")
        return view_func(request, *args, **kwargs)

    return wrapper


def _is_ai_available() -> bool:
    """Check if AI features are available (key configured AND valid)."""
    settings = AppSettings.get()
    if not settings.openrouter_api_key:
        return False
    is_valid, _ = OpenRouterService.validate_key_cached()
    return is_valid


def device_pair(request):
    """Device pairing screen for passkey mode."""
    if django_settings.AUTH_MODE != "passkey":
        return redirect("legacy:profile_selector")
    return render(request, "legacy/device_pair.html")


def profile_selector(request):
    """Profile selector screen. In passkey mode, redirects to device pairing."""
    if django_settings.AUTH_MODE == "passkey":
        return redirect("legacy:device_pair")
    profiles = list(Profile.objects.all().values("id", "name", "avatar_color", "theme", "unit_preference"))
    return render(
        request,
        "legacy/profile_selector.html",
        {
            "profiles": profiles,
        },
    )


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
        },
    )


@require_profile
def settings(request):
    """Settings screen - AI prompts and sources configuration."""
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
                "theme": profile.theme,
                "unit_preference": profile.unit_preference,
            },
            "current_profile_id": profile.id,
            "ai_available": ai_available,
            "is_admin": getattr(request, "is_admin", False),
            "default_model": app_settings.default_ai_model,
            "prompts": prompts,
            "models": models,
        },
    )
