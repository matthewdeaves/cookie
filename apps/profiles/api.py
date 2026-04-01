import os
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.db.models import Count, Q
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import AdminAuth, SessionAuth
from .models import Profile

router = Router(tags=["profiles"])


class ProfileIn(Schema):
    name: str
    avatar_color: str = ""
    theme: str = "light"
    unit_preference: str = "metric"


class ProfileOut(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str
    is_admin: Optional[bool] = None


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
    unlimited_ai: bool = False
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


class SetUnlimitedIn(Schema):
    unlimited: bool


class RenameIn(Schema):
    name: str


class ErrorSchema(Schema):
    error: str
    message: str


def _resolve_authenticated_user(request):
    """Resolve the authenticated user in passkey mode. Returns (user, profile) or (None, None)."""
    user = getattr(request, "user", None)
    if user and getattr(user, "is_authenticated", False):
        try:
            return user, user.profile
        except Profile.DoesNotExist:
            return None, None

    # Fallback: resolve from session profile_id
    profile_id = request.session.get("profile_id")
    if profile_id:
        try:
            p = Profile.objects.select_related("user").get(id=profile_id)
            if p.user and p.user.is_active:
                return p.user, p
        except Profile.DoesNotExist:
            pass
    return None, None


def _check_profile_ownership(request, profile_id):
    """In passkey mode, verify the user owns the profile (or is admin). Returns error tuple or None."""
    if settings.AUTH_MODE != "passkey":
        return None
    user, own_profile = _resolve_authenticated_user(request)
    if not user:
        return 404, {"error": "not_found", "message": "Profile not found"}
    if user.is_staff:
        return None  # Admin can access any profile
    if not own_profile or own_profile.id != profile_id:
        return 404, {"error": "not_found", "message": "Profile not found"}
    return None


@router.get("/", response=List[ProfileWithStatsSchema], auth=SessionAuth())
def list_profiles(request):
    """List all profiles with stats.

    Passkey mode: returns only current user's profile (admin sees all).
    Home mode: returns all profiles.
    """
    from apps.recipes.models import RecipeCollectionItem

    profiles = Profile.objects.annotate(
        favorites_count=Count("favorites", distinct=True),
        collections_count=Count("collections", distinct=True),
        remixes_count=Count("remixes", filter=Q(remixes__is_remix=True), distinct=True),
        view_history_count=Count("view_history", distinct=True),
        scaling_cache_count=Count("serving_adjustments", distinct=True),
        discover_cache_count=Count("ai_discovery_suggestions", distinct=True),
    ).order_by("-created_at")

    if settings.AUTH_MODE == "passkey":
        user, _ = _resolve_authenticated_user(request)
        if not user:
            return []
        if not user.is_staff:
            profiles = profiles.filter(user=user)

    result = []
    for p in profiles:
        collection_items_count = RecipeCollectionItem.objects.filter(collection__profile=p).count()

        result.append(
            ProfileWithStatsSchema(
                id=p.id,
                name=p.name,
                avatar_color=p.avatar_color,
                theme=p.theme,
                unit_preference=p.unit_preference,
                unlimited_ai=p.unlimited_ai,
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


@router.post("/", response={201: ProfileOut, 404: ErrorSchema, 429: ErrorSchema})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def create_profile(request, payload: ProfileIn):
    """Create a new profile. Only available in home mode."""
    if getattr(request, "limited", False):
        return 429, {"error": "rate_limited", "message": "Too many requests. Please try again later."}
    if settings.AUTH_MODE != "home":
        return 404, {"error": "not_found", "message": "Not found"}
    data = payload.dict()
    if not data.get("avatar_color"):
        data["avatar_color"] = Profile.next_avatar_color()
    profile = Profile.objects.create(**data)
    return 201, profile


@router.get("/{profile_id}/", response={200: ProfileOut, 404: ErrorSchema}, auth=SessionAuth())
def get_profile(request, profile_id: int):
    """Get a profile by ID. Public mode: own profile only (admin: any)."""
    ownership_error = _check_profile_ownership(request, profile_id)
    if ownership_error:
        return ownership_error
    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}


@router.put("/{profile_id}/", response={200: ProfileOut, 404: ErrorSchema}, auth=SessionAuth())
def update_profile(request, profile_id: int, payload: ProfileIn):
    """Update a profile. Public mode: own profile only (admin: any)."""
    ownership_error = _check_profile_ownership(request, profile_id)
    if ownership_error:
        return ownership_error
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}
    for key, value in payload.dict().items():
        setattr(profile, key, value)
    profile.save()
    return profile


@router.get(
    "/{profile_id}/deletion-preview/", response={200: DeletionPreviewSchema, 404: ErrorSchema}, auth=SessionAuth()
)
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted. Public mode: own profile only."""
    from apps.ai.models import AIDiscoverySuggestion
    from apps.recipes.models import (
        Recipe,
        RecipeCollection,
        RecipeCollectionItem,
        RecipeFavorite,
        RecipeViewHistory,
        ServingAdjustment,
    )

    ownership_error = _check_profile_ownership(request, profile_id)
    if ownership_error:
        return ownership_error

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}

    remixes = Recipe.objects.filter(is_remix=True, remix_profile=profile)
    favorites = RecipeFavorite.objects.filter(profile=profile)
    collections = RecipeCollection.objects.filter(profile=profile)
    collection_items = RecipeCollectionItem.objects.filter(collection__profile=profile)
    view_history = RecipeViewHistory.objects.filter(profile=profile)
    scaling_cache = ServingAdjustment.objects.filter(profile=profile)
    discover_cache = AIDiscoverySuggestion.objects.filter(profile=profile)
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


@router.delete("/{profile_id}/", response={204: None, 400: ErrorSchema, 404: ErrorSchema}, auth=SessionAuth())
def delete_profile(request, profile_id: int):
    """Delete a profile and ALL associated data.

    In passkey mode: own profile only, also cascades to delete the Django User.
    """
    from apps.recipes.models import Recipe

    ownership_error = _check_profile_ownership(request, profile_id)
    if ownership_error:
        return ownership_error

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}

    current_profile_id = request.session.get("profile_id")
    if current_profile_id == profile_id:
        request.session.pop("profile_id", None)

    # Collect image paths BEFORE cascade delete
    remix_images = list(
        Recipe.objects.filter(is_remix=True, remix_profile=profile, image__isnull=False)
        .exclude(image="")
        .values_list("image", flat=True)
    )

    if settings.AUTH_MODE == "passkey" and profile.user:
        profile.user.delete()
        request.session.flush()
    else:
        profile.delete()

    for image_path in remix_images:
        full_path = os.path.join(settings.MEDIA_ROOT, str(image_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            pass

    return 204, None


@router.post("/{profile_id}/select/", response={200: ProfileOut, 404: dict})
def select_profile(request, profile_id: int):
    """Set a profile as the current profile. Only available in home mode."""
    if settings.AUTH_MODE != "home":
        return 404, {"detail": "Not found"}
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        request.session.pop("profile_id", None)
        return 404, {"detail": "Profile not found"}
    request.session["profile_id"] = profile.id
    return profile


@router.post("/{profile_id}/set-unlimited/", response={200: dict, 404: ErrorSchema}, auth=AdminAuth())
def set_unlimited(request, profile_id: int, data: SetUnlimitedIn):
    """Set or revoke unlimited AI access for a profile. Admin only."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}
    profile.unlimited_ai = data.unlimited
    profile.save(update_fields=["unlimited_ai"])
    return {"id": profile.id, "name": profile.name, "unlimited_ai": profile.unlimited_ai}


@router.patch("/{profile_id}/rename/", response={200: dict, 400: ErrorSchema, 404: ErrorSchema}, auth=AdminAuth())
def rename_profile(request, profile_id: int, data: RenameIn):
    """Rename a profile. Admin only."""
    name = data.name.strip()
    if not name or len(name) > 100:
        return 400, {"error": "validation_error", "message": "Name must be between 1 and 100 characters"}
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {"error": "not_found", "message": "Profile not found"}
    profile.name = name
    profile.save(update_fields=["name"])
    return {"id": profile.id, "name": profile.name, "avatar_color": profile.avatar_color}
