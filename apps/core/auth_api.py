"""Authentication API endpoints — shared endpoints for passkey mode."""

import logging

from django.conf import settings
from django.contrib.auth import logout
from django.http import Http404
from ninja import Router, Status

from apps.core.auth import SessionAuth
from apps.core.auth_helpers import passkey_user_profile_response
from apps.profiles.deletion import (
    collect_remix_image_paths,
    get_deletion_preview,
    remove_remix_image_files,
)
from apps.profiles.models import Profile

security_logger = logging.getLogger("security")

router = Router(tags=["auth"])


def _require_auth_mode(request):
    """Raise 404 if not in passkey mode (the only mode with user accounts)."""
    if settings.AUTH_MODE != "passkey":
        raise Http404


# --- Endpoints ---


@router.post("/logout/", response={200: dict}, auth=SessionAuth())
def logout_view(request):
    _require_auth_mode(request)
    username = getattr(request, "user", None)
    username = username.username if username and hasattr(username, "username") else "unknown"
    logout(request)
    request.session.flush()
    security_logger.info("Logout: user=%s", username)
    return {"message": "Logged out successfully"}


@router.get("/me/", response={200: dict, 401: dict}, auth=SessionAuth())
def get_me(request):
    _require_auth_mode(request)
    user = request.user
    if not user or not getattr(user, "is_authenticated", False):
        return Status(401, {"error": "Authentication required"})

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return Status(401, {"error": "Authentication required"})

    return Status(200, passkey_user_profile_response(user, profile))


@router.get(
    "/me/deletion-preview/",
    response={200: dict, 401: dict},
    auth=SessionAuth(),
)
def get_me_deletion_preview(request):
    """Preview the data that will be removed if the caller deletes their
    own account. Passkey-mode counterpart of
    `GET /api/profiles/{id}/deletion-preview/` (which is HomeOnly)."""
    _require_auth_mode(request)
    user = request.user
    if not user or not getattr(user, "is_authenticated", False):
        return Status(401, {"error": "Authentication required"})
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return Status(401, {"error": "Authentication required"})
    return Status(200, get_deletion_preview(profile))


@router.delete(
    "/me/",
    response={204: None, 401: dict},
    auth=SessionAuth(),
)
def delete_me(request):
    """Delete the caller's own account and all associated data. Passkey-mode
    counterpart of `DELETE /api/profiles/{id}/` (which is HomeOnly).

    Deletes, in order:
      1. Snapshots remix image paths from the DB.
      2. Deletes the User, which CASCADE-drops the Profile and all its
         associated Recipe/Collection/Favorite/etc. rows.
      3. Best-effort removes remix image files from media storage.
      4. Flushes the session so the now-invalid cookie is 401 on replay.

    Step ordering is deliberate: DB first (atomic), media cleanup after
    (best-effort). A mid-delete crash leaves orphan image files — fine —
    rather than orphan DB rows.
    """
    _require_auth_mode(request)
    user = request.user
    if not user or not getattr(user, "is_authenticated", False):
        return Status(401, {"error": "Authentication required"})
    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return Status(401, {"error": "Authentication required"})

    username = user.username
    image_paths = collect_remix_image_paths(profile)
    # Deleting the User CASCADEs the Profile via its OneToOne FK.
    user.delete()
    remove_remix_image_files(image_paths)
    request.session.flush()
    security_logger.info("Self-delete: user=%s", username)
    return Status(204, None)
