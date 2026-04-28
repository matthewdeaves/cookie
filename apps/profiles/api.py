from datetime import datetime
from typing import List, Optional

from django.conf import settings
from django.db.models import Count, Q
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from apps.core.auth import HomeOnlyAnonAuth, HomeOnlyAuth, SessionAuth
from .deletion import (
    collect_remix_image_paths,
    get_deletion_preview as _build_deletion_preview,
    remove_remix_image_files,
)
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


class PreferencesIn(Schema):
    """Display-preference payload for per-profile self-updates in both modes.

    Separated from ProfileIn so passkey-mode users can change their own theme
    without touching identity fields (name, avatar_color) which remain
    HomeOnly. Every field is optional — only sent fields are written, so
    PATCH with {"theme": "dark"} is a noop on other fields.

    Note: unit_preference is accepted to preserve API back-compat for older
    clients but the endpoint rejects writes (feature disabled in v1.64). The
    underlying column remains for read-only consumers (AI scaling).
    """

    theme: Optional[str] = None
    unit_preference: Optional[str] = None


class ErrorSchema(Schema):
    error: str
    message: str


@router.get("/", response=List[ProfileWithStatsSchema], auth=HomeOnlyAnonAuth())
def list_profiles(request):
    """List all profiles with stats.

    Home mode only — profile-selection screen, runs before any session exists.
    HomeOnlyAnonAuth short-circuits to 404 in non-home modes via the route-gate
    middleware (above URL dispatch), so probes cannot distinguish this path
    from never-existed paths.
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


@router.post("/", response={201: ProfileOut, 404: ErrorSchema, 429: ErrorSchema}, auth=HomeOnlyAnonAuth())
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def create_profile(request, payload: ProfileIn):
    """Create a new profile. Home mode only — profile creation flow runs pre-session.

    CSRF is enforced by HomeOnlyAnonAuth (via APIKeyCookie._get_key); mode-gate
    short-circuits passkey probes to 404 above URL dispatch.
    """
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


@router.patch(
    "/{profile_id}/preferences/",
    response={200: ProfileOut, 400: ErrorSchema, 403: ErrorSchema, 404: ErrorSchema},
    auth=SessionAuth(),
)
def update_preferences(request, profile_id: int, payload: PreferencesIn):
    """Update only display preferences (theme, unit_preference) for the
    caller's own profile. Works in both home and passkey modes because the
    identity fields (name, avatar_color) are NOT writable here — only
    per-user display settings are. Callers must own the target profile.

    Why this exists separately from PUT /profiles/{id}/:
    In passkey mode the PUT variant is HomeOnlyAuth-gated (404) because
    profile identity is tied to the authenticated passkey user and cannot
    be reassigned mid-session. But users still need to flip dark-mode and
    change unit preferences — those are personal display settings, not
    identity. Round 10 regression guard: before this endpoint existed,
    `toggleTheme` called PUT /profiles/{id}/ which 404'd in passkey mode,
    making the UI briefly flip theme then roll back on the caught error.
    """
    # Ownership check: caller's profile.id must match the target.
    caller_profile = request.auth
    if not caller_profile or caller_profile.id != profile_id:
        return Status(403, {"error": "forbidden", "message": "Cannot modify another profile"})

    # Reject unit_preference writes — UI toggle hidden in v1.64 because conversion
    # is only wired into AI scaling, not recipe display / scrape / cook mode.
    if payload.unit_preference is not None:
        return Status(
            400,
            {"error": "feature_disabled", "message": "unit_preference is not currently configurable"},
        )

    # Validate allowed values. Reject unknown theme strings — no free-form input.
    updates: dict[str, str] = {}
    if payload.theme is not None:
        if payload.theme not in ("light", "dark"):
            return Status(400, {"error": "validation_error", "message": "theme must be 'light' or 'dark'"})
        updates["theme"] = payload.theme

    if not updates:
        # Nothing sent — return current profile, don't touch the DB.
        return caller_profile

    for key, value in updates.items():
        setattr(caller_profile, key, value)
    caller_profile.save(update_fields=list(updates.keys()))
    return caller_profile


@router.get(
    "/{profile_id}/deletion-preview/", response={200: DeletionPreviewSchema, 404: ErrorSchema}, auth=HomeOnlyAuth()
)
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted. Home mode only."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})
    return _build_deletion_preview(profile)


@router.delete("/{profile_id}/", response={204: None, 400: ErrorSchema, 404: ErrorSchema}, auth=HomeOnlyAuth())
def delete_profile(request, profile_id: int):
    """Delete a profile and ALL associated data. Home mode only (404 in passkey via HomeOnlyAuth)."""
    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": "Profile not found"})

    current_profile_id = request.session.get("profile_id")
    if current_profile_id == profile_id:
        request.session.pop("profile_id", None)

    image_paths = collect_remix_image_paths(profile)
    profile.delete()
    remove_remix_image_files(image_paths)

    return Status(204, None)


@router.post("/{profile_id}/select/", response={200: ProfileOut, 404: dict}, auth=HomeOnlyAnonAuth())
def select_profile(request, profile_id: int):
    """Set a profile as the current profile. Home mode only (pre-session selection).

    CSRF is enforced by HomeOnlyAnonAuth (via APIKeyCookie._get_key); mode-gate
    short-circuits passkey probes to 404 above URL dispatch.
    """
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
