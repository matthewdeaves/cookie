"""Tips generation service using AI."""

import logging

from apps.recipes.models import Recipe

from ..models import AIPrompt
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)


def generate_tips(recipe_id: int) -> dict:
    """Generate cooking tips for a recipe.

    Tips are cached in the Recipe.ai_tips field for efficiency.

    Args:
        recipe_id: The ID of the recipe to generate tips for.

    Returns:
        Dict with tips array and cache status.

    Raises:
        Recipe.DoesNotExist: If recipe not found.
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    recipe = Recipe.objects.get(id=recipe_id)

    # Check for cached tips
    if recipe.ai_tips:
        logger.info(f"Returning cached tips for recipe {recipe_id}")
        return {
            "tips": recipe.ai_tips,
            "cached": True,
        }

    # Get the tips_generation prompt
    prompt = AIPrompt.get_prompt("tips_generation")

    # Format ingredients as a string
    ingredients_str = "\n".join(f"- {ing}" for ing in recipe.ingredients)

    # Format instructions
    if isinstance(recipe.instructions, list):
        instructions_str = "\n".join(
            f"{i + 1}. {step.get('text', step) if isinstance(step, dict) else step}"
            for i, step in enumerate(recipe.instructions)
        )
    else:
        instructions_str = recipe.instructions_text or str(recipe.instructions)

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        title=recipe.title,
        ingredients=ingredients_str,
        instructions=instructions_str,
    )

    # Call AI service
    service = OpenRouterService()
    response = service.complete(
        system_prompt=prompt.system_prompt,
        user_prompt=user_prompt,
        model=prompt.model,
        json_response=True,
    )

    # Validate response - tips_generation returns an array directly
    validator = AIResponseValidator()
    tips = validator.validate("tips_generation", response)

    # Cache the tips on the recipe
    recipe.ai_tips = tips
    recipe.save(update_fields=["ai_tips"])

    logger.info(f"Generated and cached {len(tips)} tips for recipe {recipe_id}")

    return {
        "tips": tips,
        "cached": False,
    }


def clear_tips(recipe_id: int) -> bool:
    """Clear cached tips for a recipe.

    Args:
        recipe_id: The ID of the recipe to clear tips for.

    Returns:
        True if tips were cleared, False if no tips existed.

    Raises:
        Recipe.DoesNotExist: If recipe not found.
    """
    recipe = Recipe.objects.get(id=recipe_id)

    if recipe.ai_tips:
        recipe.ai_tips = []
        recipe.save(update_fields=["ai_tips"])
        logger.info(f"Cleared tips for recipe {recipe_id}")
        return True

    return False
