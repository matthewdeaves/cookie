"""AI discover suggestions API endpoints."""

import logging
from typing import List

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.profiles.models import Profile

from .api import ErrorOut, handle_ai_errors
from .services.discover import get_discover_suggestions

security_logger = logging.getLogger("security")

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


@router.get("/discover/{profile_id}/", response={200: DiscoverOut, 404: ErrorOut, 429: dict, 503: ErrorOut})
@ratelimit(key="ip", rate="20/h", method="GET", block=False)
@handle_ai_errors
def discover_endpoint(request, profile_id: int, refresh: bool = False):
    """Get AI discovery suggestions for a profile.

    Returns cached suggestions if still valid (within 24 hours),
    otherwise generates new suggestions via AI.

    For new users (no favorites), only seasonal suggestions are returned.
    Pass ?refresh=true to force regeneration.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/discover from %s", request.META.get("REMOTE_ADDR"))
        return 429, {"error": "rate_limited", "message": "Too many requests. Please try again later."}
    try:
        result = get_discover_suggestions(profile_id, force_refresh=refresh)
        return result
    except Profile.DoesNotExist:
        return 404, {
            "error": "not_found",
            "message": f"Profile {profile_id} not found",
        }
