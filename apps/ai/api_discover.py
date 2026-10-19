"""AI discover suggestions API endpoints."""

from datetime import timedelta
from typing import List

from django.conf import settings
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from apps.core.auth import SessionAuth
from apps.profiles.models import Profile

from .api import ErrorOut, handle_ai_errors
from .models import AIDiscoverySuggestion
from .services.discover import get_discover_suggestions, CACHE_DURATION_HOURS
from .services.feature_run import AIFeatureError, Ran, rate_limited_response, run_charged

router = Router(tags=["ai"])


# Schemas


class DiscoverSuggestionOut(Schema):
    type: str
    title: str
    description: str
    search_query: str


class DiscoverOut(Schema):
    suggestions: List[DiscoverSuggestionOut]
    refreshed_at: str


# Endpoints


@router.get(
    "/discover/{profile_id}/", response={200: DiscoverOut, 404: ErrorOut, 429: dict, 503: ErrorOut}, auth=SessionAuth()
)
@ratelimit(key="ip", rate="20/h", method="GET", block=False)
@handle_ai_errors
def discover_endpoint(request, profile_id: int, refresh: bool = False):
    """Get AI discovery suggestions for a profile.

    Returns cached suggestions if still valid (within 24 hours),
    otherwise generates new suggestions via AI.

    For new users (no favorites), only seasonal suggestions are returned.
    Pass ?refresh=true to force regeneration.
    """
    limited = rate_limited_response(request)
    if limited is not None:
        return limited

    # In passkey mode, a profile may only read its own suggestions
    if settings.AUTH_MODE != "home" and request.auth.id != profile_id:
        return Status(404, {"error": "not_found", "message": "Not found"})

    try:
        profile = Profile.objects.select_related("user").get(pk=profile_id)
    except Profile.DoesNotExist:
        return Status(404, {"error": "not_found", "message": f"Profile {profile_id} not found"})

    # Only count against quota when Anthropic is actually called (not cache hits)
    cache_cutoff = timezone.now() - timedelta(hours=CACHE_DURATION_HOURS)
    recent = AIDiscoverySuggestion.objects.filter(profile=profile, created_at__gte=cache_cutoff)
    has_cached = not refresh and recent.exists()

    def work():
        try:
            return Ran(get_discover_suggestions(profile_id, force_refresh=refresh), called_ai=not has_cached)
        except Profile.DoesNotExist as exc:
            raise AIFeatureError(404, "not_found", f"Profile {profile_id} not found") from exc

    def stale_fallback():
        # Quota exhausted: serve cached suggestions if any (e.g. refresh requested but already refreshed today)
        return get_discover_suggestions(profile_id, force_refresh=False) if recent.exists() else None

    return run_charged(profile, "discover", work, charge=not has_cached, fallback=stale_fallback)
