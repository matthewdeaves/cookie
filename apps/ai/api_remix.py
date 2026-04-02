"""AI remix API endpoints."""

import logging
from typing import List, Optional

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from apps.core.auth import SessionAuth
from apps.recipes.models import Recipe

from .api import ErrorOut, handle_ai_errors
from .services.cache import is_ai_cache_hit
from .services.quota import release_quota, reserve_quota
from .services.remix import get_remix_suggestions, create_remix

security_logger = logging.getLogger("security")

router = Router(tags=["ai"])


# Schemas


class RemixSuggestionsIn(Schema):
    recipe_id: int


class RemixSuggestionsOut(Schema):
    suggestions: List[str]


class CreateRemixIn(Schema):
    recipe_id: int
    modification: str
    profile_id: int


class RemixOut(Schema):
    id: int
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    host: str
    site_name: str
    is_remix: bool
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    yields: str = ""
    servings: Optional[int] = None


# Endpoints


@router.post(
    "/remix-suggestions",
    response={200: RemixSuggestionsOut, 400: ErrorOut, 404: ErrorOut, 429: dict, 503: ErrorOut},
    auth=SessionAuth(),
)
@ratelimit(key="ip", rate="30/h", method="POST", block=False)
@handle_ai_errors
def remix_suggestions(request, data: RemixSuggestionsIn):
    """Get 6 AI-generated remix suggestions for a recipe.

    Only works for recipes owned by the requesting profile.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/remix-suggestions from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})

    allowed, info = reserve_quota(request.auth, "remix_suggestions")
    if not allowed:
        return Status(429, {"error": "quota_exceeded", "message": "Daily limit reached for remix_suggestions", **info})

    from apps.profiles.utils import get_current_profile_or_none

    profile = get_current_profile_or_none(request)

    try:
        recipe = Recipe.objects.get(id=data.recipe_id)
    except Recipe.DoesNotExist:
        release_quota(request.auth, "remix_suggestions")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    if not profile or recipe.profile_id != profile.id:
        release_quota(request.auth, "remix_suggestions")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    was_cached = is_ai_cache_hit("remix_suggestions", data.recipe_id)
    try:
        suggestions = get_remix_suggestions(data.recipe_id)
    except Exception:
        release_quota(request.auth, "remix_suggestions")
        raise
    if was_cached:
        release_quota(request.auth, "remix_suggestions")
    return {"suggestions": suggestions}


@router.post(
    "/remix", response={200: RemixOut, 400: ErrorOut, 404: ErrorOut, 429: dict, 503: ErrorOut}, auth=SessionAuth()
)
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
@handle_ai_errors
def create_remix_endpoint(request, data: CreateRemixIn):
    """Create a remixed recipe using AI.

    Only works for recipes owned by the requesting profile.
    The remix will be owned by the same profile.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/remix from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})

    allowed, info = reserve_quota(request.auth, "remix")
    if not allowed:
        return Status(429, {"error": "quota_exceeded", "message": "Daily limit reached for remix", **info})

    from apps.profiles.utils import get_current_profile_or_none

    profile = get_current_profile_or_none(request)

    if not profile:
        release_quota(request.auth, "remix")
        return Status(
            404,
            {
                "error": "not_found",
                "message": "Profile not found",
            },
        )

    # Verify the profile_id in the request matches the session profile
    if data.profile_id != profile.id:
        release_quota(request.auth, "remix")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Profile {data.profile_id} not found",
            },
        )

    try:
        recipe = Recipe.objects.get(id=data.recipe_id)
    except Recipe.DoesNotExist:
        release_quota(request.auth, "remix")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    if recipe.profile_id != profile.id:
        release_quota(request.auth, "remix")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    try:
        remix = create_remix(
            recipe_id=data.recipe_id,
            modification=data.modification,
            profile=profile,
        )
    except Exception:
        release_quota(request.auth, "remix")
        raise
    return {
        "id": remix.id,
        "title": remix.title,
        "description": remix.description,
        "ingredients": remix.ingredients,
        "instructions": remix.instructions,
        "host": remix.host,
        "site_name": remix.site_name,
        "is_remix": remix.is_remix,
        "prep_time": remix.prep_time,
        "cook_time": remix.cook_time,
        "total_time": remix.total_time,
        "yields": remix.yields,
        "servings": remix.servings,
    }
