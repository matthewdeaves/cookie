import os
from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.db.models import Count, Q
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from ninja.errors import HttpError

from apps.core.auth import HomeOnlyAuth
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


@router.get("/", response=List[ProfileWithStatsSchema])
def list_profiles(request):
    """List all profiles with stats.

    Home mode only — this is the profile-selection screen and runs before any
    session exists, so it uses `auth=None` + inline mode check rather than
    HomeOnlyAuth (which would require a session). Returns 404 in passkey mode
    (every /api/profiles/* endpoint is home-only per spec 014-remove-is-staff).
    """
    if settings.AUTH_MODE != "home":
        raise HttpError(404, "Not found")

    from apps.recipes.models import RecipeCollectionItem

    profiles = Profile.objects.annotate(
        favorites_count=Count("favorites", distinct=True),
        collections_count=Count("collections", distinct=True),
        remixes_count=Count("remixes", filter=Q(remixes__is_remix=True), distinct=True),
        view_history_count=Count("view_history", distinct=True),
        scaling_cache_count=Count("serving_adjustments", distinct=True),
        discover_cache_count=Count("ai_discovery_suggestions", distinct=True),
    ).order_by("-created_at")

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


@router.post("/", response={201: ProfileOut, 403: ErrorSchema, 404: ErrorSchema, 429: ErrorSchema})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def create_profile(request, payload: ProfileIn):
    """Create a new profile. Home mode only — profile creation flow runs pre-session."""
    if settings.AUTH_MODE != "home":
        raise HttpError(404, "Not found")
    from django.middleware.csrf import CsrfViewMiddleware

    csrf_middleware = CsrfViewMiddleware(lambda r: None)
    csrf_middleware.process_request(request)
    reason = csrf_middleware.process_view(request, None, (), {})
    if reason:
        return Status(403, {"error": "csrf_failed", "message": "CSRF token missing or invalid"})
    if getattr(request, "limited", False):
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})
    data = payload.dict()
    if not data.get("avatar_color"):
        data["avatar_color"] = Profile.next_avatar_color()
    profile = Profile.objects.create(**data)
    return Status(201, profile)


@router.get("/{profile_id}/", response={200: ProfileOut, 404: ErrorSchema}, auth=HomeOnlyAuth())
def get_profile(request, profile_id: int):
    """Get a profile by ID. Home mode only (404 in passkey via HomeOnlyAuth)."""
    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})


@router.put("/{profile_id}/", response={200: ProfileOut, 404: ErrorSchema}, auth=HomeOnlyAuth())
def update_profile(request, profile_id: int, payload: ProfileIn):
    """Update a profile. Home mode only (404 in passkey via HomeOnlyAuth)."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})
    for key, value in payload.dict().items():
        setattr(profile, key, value)
    profile.save()
    return profile


@router.get(
    "/{profile_id}/deletion-preview/", response={200: DeletionPreviewSchema, 404: ErrorSchema}, auth=HomeOnlyAuth()
)
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted. Home mode only."""
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
        return Status(404, {"error": "not_found", "message": "Profile not found"})

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


@router.delete("/{profile_id}/", response={204: None, 400: ErrorSchema, 404: ErrorSchema}, auth=HomeOnlyAuth())
def delete_profile(request, profile_id: int):
    """Delete a profile and ALL associated data. Home mode only (404 in passkey via HomeOnlyAuth)."""
    from apps.recipes.models import Recipe

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})

    current_profile_id = request.session.get("profile_id")
    if current_profile_id == profile_id:
        request.session.pop("profile_id", None)

    # Collect image paths BEFORE cascade delete
    remix_images = list(
        Recipe.objects.filter(is_remix=True, remix_profile=profile, image__isnull=False)
        .exclude(image="")
        .values_list("image", flat=True)
    )

    profile.delete()

    for image_path in remix_images:
        full_path = os.path.join(settings.MEDIA_ROOT, str(image_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            pass

    return Status(204, None)


@router.post("/{profile_id}/select/", response={200: ProfileOut, 403: dict, 404: dict})
def select_profile(request, profile_id: int):
    """Set a profile as the current profile. Home mode only (pre-session selection)."""
    if settings.AUTH_MODE != "home":
        raise HttpError(404, "Not found")
    from django.middleware.csrf import CsrfViewMiddleware

    csrf_middleware = CsrfViewMiddleware(lambda r: None)
    csrf_middleware.process_request(request)
    reason = csrf_middleware.process_view(request, None, (), {})
    if reason:
        return Status(403, {"detail": "CSRF token missing or invalid"})
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        request.session.pop("profile_id", None)
        return Status(404, {"detail": "Profile not found"})
    request.session["profile_id"] = profile.id
    return profile


@router.post("/{profile_id}/set-unlimited/", response={200: dict, 404: ErrorSchema}, auth=HomeOnlyAuth())
def set_unlimited(request, profile_id: int, data: SetUnlimitedIn):
    """Set or revoke unlimited AI access for a profile. Admin only."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})
    profile.unlimited_ai = data.unlimited
    profile.save(update_fields=["unlimited_ai"])
    return {"id": profile.id, "name": profile.name, "unlimited_ai": profile.unlimited_ai}


@router.patch("/{profile_id}/rename/", response={200: dict, 400: ErrorSchema, 404: ErrorSchema}, auth=HomeOnlyAuth())
def rename_profile(request, profile_id: int, data: RenameIn):
    """Rename a profile. Admin only."""
    name = data.name.strip()
    if not name or len(name) > 100:
        return Status(400, {"error": "validation_error", "message": "Name must be between 1 and 100 characters"})
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})
    profile.name = name
    profile.save(update_fields=["name"])
    return {"id": profile.id, "name": profile.name, "avatar_color": profile.avatar_color}
