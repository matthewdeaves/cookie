"""Session-based authentication for Django Ninja endpoints."""

from typing import Any, Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

from apps.profiles.models import Profile


class SessionAuth(APIKeyCookie):
    """Authenticator that checks session-based profile_id.

    Cookie uses profile-based sessions (not Django auth). This checks
    that a valid profile_id exists in the session.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        profile_id = request.session.get("profile_id")
        if not profile_id:
            return None
        try:
            return Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            return None
