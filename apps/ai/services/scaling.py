"""Serving adjustment (scaling) service using AI."""

import logging

from apps.recipes.models import Recipe, ServingAdjustment
from apps.profiles.models import Profile

from ..models import AIPrompt
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)


def scale_recipe(
    recipe_id: int,
    target_servings: int,
    profile: Profile,
    unit_system: str = 'metric',
) -> dict:
    """Scale a recipe to a different number of servings.

    Args:
        recipe_id: The ID of the recipe to scale.
        target_servings: The desired number of servings.
        profile: The profile requesting the adjustment.
        unit_system: 'metric' or 'imperial'.

    Returns:
        Dict with scaled ingredients, notes, and cache status.

    Raises:
        Recipe.DoesNotExist: If recipe not found.
        ValueError: If recipe has no servings or target is invalid.
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    recipe = Recipe.objects.get(id=recipe_id)

    if not recipe.servings:
        raise ValueError('Recipe does not have serving information')

    if target_servings < 1:
        raise ValueError('Target servings must be at least 1')

    # Check for cached adjustment
    try:
        cached = ServingAdjustment.objects.get(
            recipe=recipe,
            profile=profile,
            target_servings=target_servings,
            unit_system=unit_system,
        )
        logger.info(f'Returning cached adjustment for recipe {recipe_id}')
        return {
            'target_servings': target_servings,
            'original_servings': recipe.servings,
            'ingredients': cached.ingredients,
            'notes': cached.notes,
            'cached': True,
        }
    except ServingAdjustment.DoesNotExist:
        pass

    # Get the serving_adjustment prompt
    prompt = AIPrompt.get_prompt('serving_adjustment')

    # Format ingredients as a string
    ingredients_str = '\n'.join(f'- {ing}' for ing in recipe.ingredients)

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        original_servings=recipe.servings,
        ingredients=ingredients_str,
        new_servings=target_servings,
    )

    # Call AI service
    service = OpenRouterService()
    response = service.complete(
        system_prompt=prompt.system_prompt,
        user_prompt=user_prompt,
        model=prompt.model,
        json_response=True,
    )

    # Validate response
    validator = AIResponseValidator()
    validated = validator.validate('serving_adjustment', response)

    ingredients = validated['ingredients']
    notes = validated.get('notes', [])

    # Cache the result
    ServingAdjustment.objects.create(
        recipe=recipe,
        profile=profile,
        target_servings=target_servings,
        unit_system=unit_system,
        ingredients=ingredients,
        notes=notes,
    )

    logger.info(f'Created serving adjustment for recipe {recipe_id} to {target_servings} servings')

    return {
        'target_servings': target_servings,
        'original_servings': recipe.servings,
        'ingredients': ingredients,
        'notes': notes,
        'cached': False,
    }


def calculate_nutrition(
    recipe: Recipe,
    original_servings: int,
    target_servings: int,
) -> dict:
    """Calculate scaled nutrition values.

    Uses simple multiplication since nutrition is typically per-serving.

    Args:
        recipe: The recipe with nutrition data.
        original_servings: Original number of servings.
        target_servings: Target number of servings.

    Returns:
        Dict with per_serving and total nutrition values.
    """
    if not recipe.nutrition:
        return {
            'per_serving': {},
            'total': {},
        }

    # Nutrition is per-serving, so per_serving stays the same
    per_serving = recipe.nutrition.copy()

    # Calculate total by multiplying by target servings
    total = {}
    for key, value in recipe.nutrition.items():
        if isinstance(value, str):
            # Try to extract numeric value and unit
            import re
            match = re.match(r'([\d.]+)\s*(.+)', value)
            if match:
                num = float(match.group(1))
                unit = match.group(2)
                total_num = num * target_servings
                # Format nicely
                if total_num == int(total_num):
                    total[key] = f'{int(total_num)} {unit}'
                else:
                    total[key] = f'{total_num:.1f} {unit}'
            else:
                total[key] = value
        elif isinstance(value, (int, float)):
            total[key] = value * target_servings
        else:
            total[key] = value

    return {
        'per_serving': per_serving,
        'total': total,
    }
