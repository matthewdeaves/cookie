"""Shared auth helper functions used by passkey_api and device_code_api."""

from django.conf import settings
from django.http import Http404


def require_passkey_mode(request):
    """Raise 404 if not in passkey mode."""
    if settings.AUTH_MODE != "passkey":
        raise Http404


def passkey_user_profile_response(user, profile):
    """Build the standard passkey-mode user/profile response dict."""
    return {
        "user": {"id": user.id},
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "avatar_color": profile.avatar_color,
            "theme": profile.theme,
            "unit_preference": profile.unit_preference,
        },
    }
