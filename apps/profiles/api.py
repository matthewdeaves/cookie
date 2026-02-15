import os
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Count, Q
from ninja import Router, Schema

from apps.core.models import AppSettings
from apps.core.utils import is_admin

from .models import Profile
from .validators import validate_registration, validate_username, validate_password

router = Router(tags=["profiles"])


class ProfileIn(Schema):
    name: str
    avatar_color: str
    theme: str = "light"
    unit_preference: str = "metric"


class ProfileOut(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str


class ProfileStatsSchema(Schema):
    favorites: int
    collections: int
    collection_items: int
    remixes: int
    view_history: int
    scaling_cache: int
    discover_cache: int


class ProfileWithStatsSchema(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str
    created_at: datetime
    stats: ProfileStatsSchema


class DeletionDataSchema(Schema):
    remixes: int
    remix_images: int
    favorites: int
    collections: int
    collection_items: int
    view_history: int
    scaling_cache: int
    discover_cache: int


class ProfileSummarySchema(Schema):
    id: int
    name: str
    avatar_color: str
    created_at: datetime


class DeletionPreviewSchema(Schema):
    profile: ProfileSummarySchema
    data_to_delete: DeletionDataSchema
    warnings: List[str]


class ErrorSchema(Schema):
    error: str
    message: str


@router.get("/", response=List[ProfileWithStatsSchema])
def list_profiles(request):
    """List all profiles with stats for user management.

    In home mode: Returns all profiles.
    In public mode:
      - Admin: Returns all profiles
      - Regular user: Returns only their own profile
    """
    from apps.recipes.models import RecipeCollectionItem

    app_settings = AppSettings.get()
    deployment_mode = app_settings.get_deployment_mode()

    profiles = Profile.objects.annotate(
        favorites_count=Count("favorites", distinct=True),
        collections_count=Count("collections", distinct=True),
        remixes_count=Count("remixes", filter=Q(remixes__is_remix=True), distinct=True),
        view_history_count=Count("view_history", distinct=True),
        scaling_cache_count=Count("serving_adjustments", distinct=True),
        discover_cache_count=Count("ai_discovery_suggestions", distinct=True),
    )

    # In public mode, non-admin users can only see their own profile
    if deployment_mode == "public" and not is_admin(request.user):
        if request.user.is_authenticated and hasattr(request.user, "profile"):
            profiles = profiles.filter(id=request.user.profile.id)
        else:
            profiles = profiles.none()

    profiles = profiles.order_by("-created_at")

    result = []
    for p in profiles:
        # Count collection items separately (requires join)
        collection_items_count = RecipeCollectionItem.objects.filter(collection__profile=p).count()

        result.append(
            ProfileWithStatsSchema(
                id=p.id,
                name=p.name,
                avatar_color=p.avatar_color,
                theme=p.theme,
                unit_preference=p.unit_preference,
                created_at=p.created_at,
                stats=ProfileStatsSchema(
                    favorites=p.favorites_count,
                    collections=p.collections_count,
                    collection_items=collection_items_count,
                    remixes=p.remixes_count,
                    view_history=p.view_history_count,
                    scaling_cache=p.scaling_cache_count,
                    discover_cache=p.discover_cache_count,
                ),
            )
        )
    return result


@router.post("/", response={201: ProfileOut})
def create_profile(request, payload: ProfileIn):
    """Create a new profile."""
    profile = Profile.objects.create(**payload.dict())
    return 201, profile


@router.get("/{profile_id}/", response=ProfileOut)
def get_profile(request, profile_id: int):
    """Get a profile by ID."""
    return Profile.objects.get(id=profile_id)


@router.put("/{profile_id}/", response=ProfileOut)
def update_profile(request, profile_id: int, payload: ProfileIn):
    """Update a profile."""
    profile = Profile.objects.get(id=profile_id)
    for key, value in payload.dict().items():
        setattr(profile, key, value)
    profile.save()
    return profile


@router.get("/{profile_id}/deletion-preview/", response={200: DeletionPreviewSchema, 404: ErrorSchema})
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted with this profile."""
    from apps.ai.models import AIDiscoverySuggestion
    from apps.recipes.models import (
        Recipe,
        RecipeCollection,
        RecipeCollectionItem,
        RecipeFavorite,
        RecipeViewHistory,
        ServingAdjustment,
    )

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}

    # Count related data
    remixes = Recipe.objects.filter(is_remix=True, remix_profile=profile)
    favorites = RecipeFavorite.objects.filter(profile=profile)
    collections = RecipeCollection.objects.filter(profile=profile)
    collection_items = RecipeCollectionItem.objects.filter(collection__profile=profile)
    view_history = RecipeViewHistory.objects.filter(profile=profile)
    scaling_cache = ServingAdjustment.objects.filter(profile=profile)
    discover_cache = AIDiscoverySuggestion.objects.filter(profile=profile)

    # Count images that will be deleted
    remix_images_count = remixes.exclude(image="").exclude(image__isnull=True).count()

    return {
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "avatar_color": profile.avatar_color,
            "created_at": profile.created_at,
        },
        "data_to_delete": {
            "remixes": remixes.count(),
            "remix_images": remix_images_count,
            "favorites": favorites.count(),
            "collections": collections.count(),
            "collection_items": collection_items.count(),
            "view_history": view_history.count(),
            "scaling_cache": scaling_cache.count(),
            "discover_cache": discover_cache.count(),
        },
        "warnings": [
            "All remixed recipes will be permanently deleted",
            "Recipe images for remixes will be removed from storage",
            "This action cannot be undone",
        ],
    }


@router.delete("/{profile_id}/", response={204: None, 400: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema})
def delete_profile(request, profile_id: int):
    """
    Delete a profile and ALL associated data.

    In home mode: Any user can delete any profile.
    In public mode:
      - Users can delete their own profile
      - Only admin can delete other users' profiles

    Cascade deletes:
    - Recipe remixes (is_remix=True, remix_profile=this)
    - Favorites
    - Collections and collection items
    - View history
    - Serving adjustment cache
    - AI discovery suggestions

    Manual cleanup:
    - Recipe images from deleted remixes
    """
    from apps.recipes.models import Recipe

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}

    # Check permissions in public mode
    app_settings = AppSettings.get()
    if app_settings.get_deployment_mode() == "public":
        # Check if user is deleting their own profile or is admin
        is_own_profile = (
            request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.id == profile_id
        )

        if not is_own_profile and not is_admin(request.user):
            return 403, {"error": "forbidden", "message": "Cannot delete another user's profile"}

    # Check if this is the current session profile
    current_profile_id = request.session.get("profile_id")
    if current_profile_id == profile_id:
        # Clear session profile
        del request.session["profile_id"]

    # Collect image paths BEFORE cascade delete
    remix_images = list(
        Recipe.objects.filter(is_remix=True, remix_profile=profile, image__isnull=False)
        .exclude(image="")
        .values_list("image", flat=True)
    )

    # Django CASCADE handles all related records
    profile.delete()

    # Clean up orphaned image files
    for image_path in remix_images:
        full_path = os.path.join(settings.MEDIA_ROOT, str(image_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            # Log but don't fail - orphaned files are non-critical
            pass

    return 204, None


@router.post("/{profile_id}/select/", response={200: ProfileOut, 401: ErrorSchema, 403: ErrorSchema})
def select_profile(request, profile_id: int):
    """Set a profile as the current profile (stored in session).

    In home mode: Any user can select any profile.
    In public mode: User must be authenticated and own the profile.
    """
    app_settings = AppSettings.get()
    deployment_mode = app_settings.get_deployment_mode()

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}

    if deployment_mode == "public":
        # Public mode: require authentication
        if not request.user.is_authenticated:
            return 401, {"error": "unauthorized", "message": "Authentication required"}

        # Public mode: user can only select their own profile
        if not hasattr(request.user, "profile") or request.user.profile.id != profile_id:
            return 403, {"error": "forbidden", "message": "Cannot select another user's profile"}

    request.session["profile_id"] = profile.id
    return profile


# ============================================================================
# Authentication API
# ============================================================================


class RegisterSchema(Schema):
    username: str
    password: str
    password_confirm: str
    avatar_color: str = "#6366f1"


class LoginSchema(Schema):
    username: str
    password: str


class AuthResponseSchema(Schema):
    profile: ProfileOut
    message: str


class ValidationErrorSchema(Schema):
    error: str
    field: Optional[str] = None


@router.post("/auth/register/", response={201: AuthResponseSchema, 400: ValidationErrorSchema, 403: ErrorSchema})
def register(request, data: RegisterSchema):
    """Register a new user account.

    Only available in public deployment mode with registration enabled.
    Creates both a User and associated Profile.
    """
    app_settings = AppSettings.get()

    # Check deployment mode
    if app_settings.get_deployment_mode() != "public":
        return 403, {"error": "forbidden", "message": "Registration not available in home mode"}

    # Check if registration is enabled
    if not app_settings.get_allow_registration():
        return 403, {"error": "forbidden", "message": "Registration is disabled"}

    # Check if already authenticated
    if request.user.is_authenticated:
        return 400, {"error": "Already authenticated", "field": None}

    # Validate using shared validators
    validation = validate_registration(
        data.username.strip(),
        data.password,
        data.password_confirm,
    )
    if not validation.is_valid:
        # Determine which field the error relates to
        field = None
        if "username" in validation.error.lower():
            field = "username"
        elif "password" in validation.error.lower():
            field = "password" if "confirm" not in validation.error.lower() else "password_confirm"
        return 400, {"error": validation.error, "field": field}

    # Create user and profile
    username = data.username.strip()
    user = User.objects.create_user(username=username, password=data.password)
    profile = Profile.objects.create(
        user=user,
        name=username,
        avatar_color=data.avatar_color,
    )

    # Log in the new user
    login(request, user)
    request.session["profile_id"] = profile.id

    return 201, {
        "profile": profile,
        "message": f"Welcome, {profile.name}!",
    }


@router.post("/auth/login/", response={200: AuthResponseSchema, 400: ValidationErrorSchema, 401: ErrorSchema})
def login_user(request, data: LoginSchema):
    """Log in with username and password.

    Only available in public deployment mode.
    """
    app_settings = AppSettings.get()

    # Check deployment mode
    if app_settings.get_deployment_mode() != "public":
        return 400, {"error": "Login not required in home mode", "field": None}

    # Check if already authenticated
    if request.user.is_authenticated:
        return 400, {"error": "Already authenticated", "field": None}

    # Authenticate user
    user = authenticate(request, username=data.username.strip(), password=data.password)

    if user is None:
        # Use same error message for all failures (prevents username enumeration)
        return 401, {"error": "unauthorized", "message": "Invalid username or password"}

    # Log in the user (regenerates session ID)
    login(request, user)

    # Set profile in session
    if hasattr(user, "profile"):
        request.session["profile_id"] = user.profile.id
        return {
            "profile": user.profile,
            "message": f"Welcome back, {user.profile.name}!",
        }

    return 401, {"error": "unauthorized", "message": "User has no profile"}


@router.post("/auth/logout/", response={200: dict})
def logout_user(request):
    """Log out the current user."""
    logout(request)
    if "profile_id" in request.session:
        del request.session["profile_id"]
    return {"message": "Logged out successfully"}
