"""Timer naming service using AI."""

import logging

from ..models import AIPrompt
from .cache import cache_ai_response, CACHE_TIMEOUT_SHORT
from .openrouter import OpenRouterService
from .validator import AIResponseValidator

logger = logging.getLogger(__name__)


@cache_ai_response("timer_name", timeout=CACHE_TIMEOUT_SHORT)
def generate_timer_name(step_text: str, duration_minutes: int) -> dict:
    """Generate a descriptive name for a cooking timer.

    Args:
        step_text: The cooking instruction text.
        duration_minutes: The timer duration in minutes.

    Returns:
        Dict with the generated label.

    Raises:
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    # Get the timer_naming prompt
    prompt = AIPrompt.get_prompt("timer_naming")

    # Format duration nicely
    if duration_minutes >= 60:
        hours = duration_minutes // 60
        mins = duration_minutes % 60
        if mins > 0:
            duration_str = f"{hours} hour{'s' if hours > 1 else ''} {mins} minute{'s' if mins > 1 else ''}"
        else:
            duration_str = f"{hours} hour{'s' if hours > 1 else ''}"
    else:
        duration_str = f"{duration_minutes} minute{'s' if duration_minutes > 1 else ''}"

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        instruction=step_text,
        duration=duration_str,
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
    result = validator.validate("timer_naming", response)

    # Truncate label if too long (max 30 chars as per spec)
    label = result["label"]
    if len(label) > 30:
        label = label[:27] + "..."

    logger.info(f'Generated timer name: "{label}" for {duration_minutes}min timer')

    return {
        "label": label,
    }
