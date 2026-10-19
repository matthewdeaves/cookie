"""AI remix API endpoints."""

from typing import List, Optional

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import SessionAuth

from .api import ErrorOut, handle_ai_errors
from .services.cache import is_ai_cache_hit
from .services.feature_run import Ran, run_ai_feature
from .services.remix import get_remix_suggestions, create_remix

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

    def work(ctx):
        was_cached = is_ai_cache_hit("remix_suggestions", data.recipe_id)
        return Ran({"suggestions": get_remix_suggestions(data.recipe_id)}, called_ai=not was_cached)

    return run_ai_feature(request, "remix_suggestions", work, recipe_id=data.recipe_id)


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

    def work(ctx):
        remix = create_remix(recipe_id=data.recipe_id, modification=data.modification, profile=ctx.profile)
        return Ran(
            {
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
        )

    return run_ai_feature(request, "remix", work, recipe_id=data.recipe_id, claimed_profile_id=data.profile_id)
