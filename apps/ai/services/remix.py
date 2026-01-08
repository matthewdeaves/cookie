"""Recipe remix service using AI."""

import logging
from typing import Any

from apps.recipes.models import Recipe
from apps.profiles.models import Profile

from ..models import AIPrompt
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)


def get_remix_suggestions(recipe_id: int) -> list[str]:
    """Get 6 AI-generated remix suggestions for a recipe.

    Args:
        recipe_id: The ID of the recipe to get suggestions for.

    Returns:
        List of 6 suggestion strings.

    Raises:
        Recipe.DoesNotExist: If recipe not found.
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    recipe = Recipe.objects.get(id=recipe_id)

    # Get the remix_suggestions prompt
    prompt = AIPrompt.get_prompt('remix_suggestions')

    # Format ingredients as a string
    ingredients_str = '\n'.join(f'- {ing}' for ing in recipe.ingredients)

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        title=recipe.title,
        cuisine=recipe.cuisine or 'Not specified',
        category=recipe.category or 'Not specified',
        ingredients=ingredients_str,
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
    validated = validator.validate('remix_suggestions', response)

    return validated


def create_remix(
    recipe_id: int,
    modification: str,
    profile: Profile,
) -> Recipe:
    """Create a remixed recipe using AI.

    Args:
        recipe_id: The ID of the original recipe to remix.
        modification: The user's requested modification.
        profile: The profile creating the remix.

    Returns:
        The newly created Recipe object.

    Raises:
        Recipe.DoesNotExist: If original recipe not found.
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    original = Recipe.objects.get(id=recipe_id)

    # Get the recipe_remix prompt
    prompt = AIPrompt.get_prompt('recipe_remix')

    # Format ingredients and instructions
    ingredients_str = '\n'.join(f'- {ing}' for ing in original.ingredients)

    if isinstance(original.instructions, list):
        # Handle structured instructions
        instructions_str = '\n'.join(
            f'{i+1}. {step.get("text", step) if isinstance(step, dict) else step}'
            for i, step in enumerate(original.instructions)
        )
    else:
        instructions_str = original.instructions_text or str(original.instructions)

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        title=original.title,
        description=original.description or 'No description',
        ingredients=ingredients_str,
        instructions=instructions_str,
        modification=modification,
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
    validated = validator.validate('recipe_remix', response)

    # Parse timing values if provided
    prep_time = _parse_time(validated.get('prep_time'))
    cook_time = _parse_time(validated.get('cook_time'))
    total_time = _parse_time(validated.get('total_time'))

    # Parse yields to servings
    yields_str = validated.get('yields', '')
    servings = _parse_servings(yields_str)

    # Create the remixed recipe
    remix = Recipe.objects.create(
        title=validated['title'],
        description=validated['description'],
        ingredients=validated['ingredients'],
        instructions=validated['instructions'],
        instructions_text='\n'.join(validated['instructions']),
        host='user-generated',
        site_name='User Generated',
        source_url=None,
        is_remix=True,
        remix_profile=profile,
        prep_time=prep_time,
        cook_time=cook_time,
        total_time=total_time,
        yields=yields_str,
        servings=servings,
        # Carry over some fields from original
        cuisine=original.cuisine,
        category=original.category,
        image_url=original.image_url,
        image=original.image,
    )

    logger.info(f'Created remix {remix.id} from recipe {original.id} for profile {profile.id}')

    return remix


def _parse_time(time_str: str | None) -> int | None:
    """Parse a time string like '30 minutes' into minutes."""
    if not time_str:
        return None

    time_str = time_str.lower().strip()

    # Try to extract numbers
    import re
    numbers = re.findall(r'\d+', time_str)
    if not numbers:
        return None

    minutes = int(numbers[0])

    # Convert hours to minutes if needed
    if 'hour' in time_str:
        minutes *= 60
        if len(numbers) > 1:
            minutes += int(numbers[1])

    return minutes


def _parse_servings(yields_str: str) -> int | None:
    """Parse a yields string like '4 servings' into an integer."""
    if not yields_str:
        return None

    import re
    numbers = re.findall(r'\d+', yields_str)
    if numbers:
        return int(numbers[0])

    return None
