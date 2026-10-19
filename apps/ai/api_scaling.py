"""AI recipe scaling API endpoints."""

from typing import List, Optional

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import SessionAuth

from .api import ErrorOut, handle_ai_errors
from .services.feature_run import AIFeatureError, Ran, run_ai_feature
from .services.scaling import scale_recipe, calculate_nutrition

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

    def work(ctx):
        try:
            result = scale_recipe(
                recipe_id=data.recipe_id,
                target_servings=data.target_servings,
                profile=ctx.profile,
                unit_system=data.unit_system,
            )
        except ValueError as e:
            raise AIFeatureError(400, "validation_error", str(e)) from e

        # Calculate nutrition if available
        recipe = ctx.recipe
        nutrition = None
        if recipe.nutrition:
            nutrition = calculate_nutrition(
                recipe=recipe,
                original_servings=recipe.servings,
                target_servings=data.target_servings,
            )

        return Ran(
            {
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
            },
            called_ai=not result.get("cached"),
        )

    return run_ai_feature(request, "scale", work, recipe_id=data.recipe_id, claimed_profile_id=data.profile_id)
