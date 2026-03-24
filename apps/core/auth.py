"""Session-based authentication for Django Ninja endpoints."""

import logging
from typing import Any, Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.security import APIKeyCookie

from apps.profiles.models import Profile

security_logger = logging.getLogger("security")


class SessionAuth(APIKeyCookie):
    """Authenticator that checks session-based profile_id.

    Cookie uses profile-based sessions (not Django auth). This checks
    that a valid profile_id exists in the session.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        profile_id = request.session.get("profile_id")
        if not profile_id:
            security_logger.warning(
                "Auth failure: no profile_id in session for %s from %s",
                request.path,
                request.META.get("REMOTE_ADDR"),
            )
            return None
        try:
            return Profile.objects.get(id=profile_id)
        except Profile.DoesNotExist:
            security_logger.warning(
                "Auth failure: invalid profile_id %s for %s from %s",
                profile_id,
                request.path,
                request.META.get("REMOTE_ADDR"),
            )
            return None
