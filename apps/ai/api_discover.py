"""AI discover suggestions API endpoints."""

from typing import List

from ninja import Router, Schema

from apps.profiles.models import Profile

from .api import ErrorOut, handle_ai_errors
from .services.discover import get_discover_suggestions

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


@router.get("/discover/{profile_id}/", response={200: DiscoverOut, 404: ErrorOut, 503: ErrorOut})
@handle_ai_errors
def discover_endpoint(request, profile_id: int):
    """Get AI discovery suggestions for a profile.

    Returns cached suggestions if still valid (within 24 hours),
    otherwise generates new suggestions via AI.

    For new users (no favorites), only seasonal suggestions are returned.
    """
    try:
        result = get_discover_suggestions(profile_id)
        return result
    except Profile.DoesNotExist:
        return 404, {
            "error": "not_found",
            "message": f"Profile {profile_id} not found",
        }
