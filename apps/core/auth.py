"""Session-based authentication for Django Ninja endpoints."""

import logging
from typing import Any, Optional

from django.conf import settings
from django.http import HttpRequest
from ninja.errors import HttpError
from ninja.security import APIKeyCookie

from apps.profiles.models import Profile

__all__ = ["SessionAuth", "AdminAuth", "HomeOnlyAdminAuth"]

security_logger = logging.getLogger("security")


class SessionAuth(APIKeyCookie):
    """Mode-aware authenticator.

    Home mode: checks session["profile_id"] → Profile (no user accounts).
    Passkey mode: checks request.user.is_authenticated → request.user.profile.
    """

    param_name: str = settings.SESSION_COOKIE_NAME

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        if settings.AUTH_MODE == "passkey":
            return self._authenticate_passkey(request)
        return self._authenticate_home(request)

    def _authenticate_home(self, request: HttpRequest) -> Optional[Profile]:
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

    def _authenticate_passkey(self, request: HttpRequest) -> Optional[Profile]:
        user = getattr(request, "user", None)
        if not user or not getattr(user, "is_authenticated", False):
            # Fallback: check session profile_id (set during passkey login)
            profile_id = request.session.get("profile_id")
            if profile_id:
                try:
                    profile = Profile.objects.select_related("user").get(id=profile_id)
                    if profile.user and profile.user.is_active:
                        request.user = profile.user
                        return profile
                except Profile.DoesNotExist:
                    pass
            security_logger.warning(
                "Auth failure: unauthenticated request to %s from %s",
                request.path,
                request.META.get("REMOTE_ADDR"),
            )
            return None
        if not user.is_active:
            return None
        try:
            return user.profile
        except Profile.DoesNotExist:
            security_logger.warning(
                "Auth failure: no profile for user %s at %s",
                user.pk,
                request.path,
            )
            return None


class AdminAuth(SessionAuth):
    """Admin-only authenticator.

    Home mode: identical to SessionAuth (no admin distinction). This is an
    accepted design decision — home mode is intended for single-household use
    where all profiles are trusted. Any profile holder can access admin
    endpoints (e.g., /api/system/reset/, /api/ai/save-api-key). This matches
    the constitution's Principle III: no authentication friction in home mode.

    Passkey mode: resolves user first, then checks is_staff. Only users
    promoted to admin via the cookie_admin CLI can access admin endpoints.
    """

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        if settings.AUTH_MODE == "passkey":
            profile = self._authenticate_passkey(request)
            if profile is None:
                return None  # 401 — not authenticated
            user = getattr(request, "user", None)
            if not user or not user.is_staff:
                security_logger.warning(
                    "Admin auth failure: %s from %s",
                    request.path,
                    request.META.get("REMOTE_ADDR"),
                )
                raise HttpError(403, "Admin access required")
            return profile
        return self._authenticate_home(request)


class HomeOnlyAdminAuth(AdminAuth):
    """AdminAuth gated by AUTH_MODE=home.

    Raises 404 before any cookie extraction or AdminAuth.authenticate() call when
    AUTH_MODE != "home". Probes from passkey deployments are indistinguishable
    from hits on a never-existed path: same status, same body, no security-log
    auth-failure line.
    """

    def __call__(self, request: HttpRequest) -> Any:
        if settings.AUTH_MODE != "home":
            raise HttpError(404, "Not found")
        return super().__call__(request)
