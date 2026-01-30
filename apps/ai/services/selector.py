"""CSS selector repair service using AI."""

import logging
from typing import Optional

from apps.recipes.models import SearchSource

from ..models import AIPrompt
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)

# Default confidence threshold for auto-updating selectors
DEFAULT_CONFIDENCE_THRESHOLD = 0.8


def repair_selector(
    source: SearchSource,
    html_sample: str,
    target: str = "recipe search result",
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    auto_update: bool = True,
) -> dict:
    """Attempt to repair a broken CSS selector using AI.

    Analyzes the provided HTML sample and suggests new CSS selectors
    that could replace the broken one.

    Args:
        source: The SearchSource with the broken selector.
        html_sample: Sample HTML from the search page (truncated to ~50KB).
        target: Description of the target element type.
        confidence_threshold: Minimum confidence to auto-update (0-1).
        auto_update: If True and confidence exceeds threshold, update the source.

    Returns:
        Dict with keys:
            - suggestions: List of suggested CSS selectors
            - confidence: AI's confidence score (0-1)
            - original_selector: The original broken selector
            - updated: Whether the source was auto-updated
            - new_selector: The new selector if updated, else None

    Raises:
        AIUnavailableError: If AI service is not available.
        AIResponseError: If AI returns invalid response.
        ValidationError: If response doesn't match expected schema.
    """
    original_selector = source.result_selector

    # Get the selector_repair prompt
    prompt = AIPrompt.get_prompt("selector_repair")

    # Truncate HTML to avoid token limits (keep first ~50KB)
    truncated_html = html_sample[:50000]

    # Format the user prompt
    user_prompt = prompt.format_user_prompt(
        selector=original_selector or "(none)",
        target=target,
        html_sample=truncated_html,
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
    validated = validator.validate("selector_repair", response)

    suggestions = validated.get("suggestions", [])
    confidence = validated.get("confidence", 0)

    result = {
        "suggestions": suggestions,
        "confidence": confidence,
        "original_selector": original_selector,
        "updated": False,
        "new_selector": None,
    }

    # Auto-update if confidence is high enough and we have suggestions
    if auto_update and suggestions and confidence >= confidence_threshold:
        new_selector = suggestions[0]
        source.result_selector = new_selector
        source.needs_attention = False  # Clear the attention flag
        source.save(update_fields=["result_selector", "needs_attention"])

        result["updated"] = True
        result["new_selector"] = new_selector

        logger.info(
            f"Auto-updated selector for {source.host}: "
            f'"{original_selector}" -> "{new_selector}" (confidence: {confidence:.2f})'
        )
    else:
        logger.info(
            f"Selector repair suggestions for {source.host} "
            f"(confidence: {confidence:.2f}, threshold: {confidence_threshold}): "
            f"{suggestions}"
        )

    return result


def get_sources_needing_attention() -> list[SearchSource]:
    """Get all SearchSources that need attention.

    Returns sources that have consecutive failures >= 3 or
    have needs_attention flag set.
    """
    return list(
        SearchSource.objects.filter(
            needs_attention=True,
            is_enabled=True,
        )
    )


def repair_all_broken_selectors(
    html_samples: dict[str, str],
    confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
) -> dict:
    """Attempt to repair all sources needing attention.

    Args:
        html_samples: Dict mapping host to HTML sample.
        confidence_threshold: Minimum confidence to auto-update.

    Returns:
        Dict with:
            - repaired: List of hosts that were successfully repaired
            - failed: List of hosts that could not be repaired
            - skipped: List of hosts with no HTML sample provided
            - results: Dict mapping host to repair result
    """
    sources = get_sources_needing_attention()

    repaired = []
    failed = []
    skipped = []
    results = {}

    for source in sources:
        host = source.host

        if host not in html_samples:
            skipped.append(host)
            continue

        try:
            result = repair_selector(
                source=source,
                html_sample=html_samples[host],
                confidence_threshold=confidence_threshold,
            )
            results[host] = result

            if result["updated"]:
                repaired.append(host)
            else:
                failed.append(host)

        except (AIUnavailableError, AIResponseError, ValidationError) as e:
            logger.error(f"Failed to repair selector for {host}: {e}")
            failed.append(host)
            results[host] = {"error": str(e)}

    return {
        "repaired": repaired,
        "failed": failed,
        "skipped": skipped,
        "results": results,
    }
