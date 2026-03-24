"""AI recipe scaling API endpoints."""

import logging
from typing import List, Optional

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import SessionAuth
from apps.recipes.models import Recipe

from .api import ErrorOut, handle_ai_errors
from .services.scaling import scale_recipe, calculate_nutrition

security_logger = logging.getLogger("security")

router = Router(tags=["ai"])


# Schemas


class ScaleIn(Schema):
    recipe_id: int
    target_servings: int
    unit_system: str = "metric"
    profile_id: int


class NutritionOut(Schema):
    per_serving: dict
    total: dict


class ScaleOut(Schema):
    target_servings: int
    original_servings: int
    ingredients: List[str]
    instructions: List[str] = []  # QA-031
    notes: List[str]
    prep_time_adjusted: Optional[int] = None  # QA-032
    cook_time_adjusted: Optional[int] = None  # QA-032
    total_time_adjusted: Optional[int] = None  # QA-032
    nutrition: Optional[NutritionOut] = None
    cached: bool


# Endpoints


@router.post(
    "/scale", response={200: ScaleOut, 400: ErrorOut, 404: ErrorOut, 429: dict, 503: ErrorOut}, auth=SessionAuth()
)
@ratelimit(key="ip", rate="30/h", method="POST", block=False)
@handle_ai_errors
def scale_recipe_endpoint(request, data: ScaleIn):
    """Scale a recipe to a different number of servings.

    Only works for recipes owned by the requesting profile.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/scale from %s", request.META.get("REMOTE_ADDR"))
        return 429, {"error": "rate_limited", "message": "Too many requests. Please try again later."}
    from apps.profiles.utils import get_current_profile_or_none

    profile = get_current_profile_or_none(request)

    if not profile:
        return 404, {
            "error": "not_found",
            "message": "Profile not found",
        }

    # Verify the profile_id in the request matches the session profile
    if data.profile_id != profile.id:
        return 404, {
            "error": "not_found",
            "message": f"Profile {data.profile_id} not found",
        }

    try:
        recipe = Recipe.objects.get(id=data.recipe_id)
    except Recipe.DoesNotExist:
        return 404, {
            "error": "not_found",
            "message": f"Recipe {data.recipe_id} not found",
        }

    if recipe.profile_id != profile.id:
        return 404, {
            "error": "not_found",
            "message": f"Recipe {data.recipe_id} not found",
        }

    try:
        result = scale_recipe(
            recipe_id=data.recipe_id,
            target_servings=data.target_servings,
            profile=profile,
            unit_system=data.unit_system,
        )
    except ValueError as e:
        return 400, {
            "error": "validation_error",
            "message": str(e),
        }

    # Calculate nutrition if available
    nutrition = None
    if recipe.nutrition:
        nutrition = calculate_nutrition(
            recipe=recipe,
            original_servings=recipe.servings,
            target_servings=data.target_servings,
        )

    return {
        "target_servings": result["target_servings"],
        "original_servings": result["original_servings"],
        "ingredients": result["ingredients"],
        "instructions": result.get("instructions", []),  # QA-031
        "notes": result["notes"],
        "prep_time_adjusted": result.get("prep_time_adjusted"),  # QA-032
        "cook_time_adjusted": result.get("cook_time_adjusted"),  # QA-032
        "total_time_adjusted": result.get("total_time_adjusted"),  # QA-032
        "nutrition": nutrition,
        "cached": result["cached"],
    }
