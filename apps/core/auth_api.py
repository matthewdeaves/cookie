"""Authentication API endpoints — shared endpoints for passkey mode."""

import logging

from django.conf import settings
from django.contrib.auth import logout
from django.http import Http404
from ninja import Router, Status

from apps.core.auth import SessionAuth
from apps.core.auth_helpers import passkey_user_profile_response
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
