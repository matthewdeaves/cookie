"""AI-powered search result ranking service."""

import logging
from typing import Any

from apps.core.models import AppSettings

from ..models import AIPrompt
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)


def is_ranking_available() -> bool:
    """Check if AI ranking is available (API key configured)."""
    try:
        settings = AppSettings.get()
        return bool(settings.openrouter_api_key)
    except Exception:
        return False


def _filter_valid(results: list[dict]) -> list[dict]:
    """Filter out results without titles (QA-053).

    Results without titles will fail to import, so they should
    never be shown to users.
    """
    return [r for r in results if r.get("title")]


def _sort_by_image(results: list[dict]) -> list[dict]:
    """Filter and sort results to prioritize those with images.

    This provides a basic image-first sorting when AI ranking
    is unavailable or fails. Also filters out invalid results.
    """
    valid_results = _filter_valid(results)
    return sorted(valid_results, key=lambda r: 0 if r.get("image_url") else 1)


def _prepare_results(results: list[dict]) -> tuple[list[dict], list[dict]]:
    """Split results into a rankable batch and remainder.

    Limits the AI ranking prompt to 40 results for manageable prompt size.
    """
    results_to_rank = results[:40]
    remaining = results[40:]
    return results_to_rank, remaining


def _build_ranking_prompt(query: str, results_to_rank: list[dict]) -> tuple[Any, str]:
    """Build the AI ranking prompt from results.

    Returns:
        Tuple of (AIPrompt, formatted user prompt string).

    Raises:
        AIPrompt.DoesNotExist: If search_ranking prompt is not configured.
    """
    prompt = AIPrompt.get_prompt("search_ranking")

    results_text = "\n".join(
        f'{i}. "{r.get("title", "Unknown")}" from {r.get("host", "unknown")} '
        f"- {r.get('description', 'No description')[:100]}"
        f"{' [has image]' if r.get('image_url') else ''}"
        for i, r in enumerate(results_to_rank)
    )

    user_prompt = prompt.format_user_prompt(
        query=query,
        results=results_text,
        count=len(results_to_rank),
    )
    return prompt, user_prompt


def _rank_with_ai(prompt: Any, user_prompt: str, results_to_rank: list[dict], remaining: list[dict]) -> list[dict]:
    """Call OpenRouter to rank results and merge with remainder.

    Raises:
        AIUnavailableError, AIResponseError, ValidationError: On AI failures.
    """
    service = OpenRouterService()
    response = service.complete(
        system_prompt=prompt.system_prompt,
        user_prompt=user_prompt,
        model=prompt.model,
        json_response=True,
    )

    validator = AIResponseValidator()
    ranking = validator.validate("search_ranking", response)
    ranked_results = _apply_ranking(results_to_rank, ranking)

    if remaining:
        remaining_sorted = sorted(remaining, key=lambda r: 0 if r.get("image_url") else 1)
        ranked_results.extend(remaining_sorted)

    return ranked_results


def rank_results(query: str, results: list[dict]) -> list[dict]:
    """Rank search results using AI.

    The AI considers:
    - Relevance to the search query
    - Recipe completeness (image, ratings)
    - Source reliability
    - Title/description clarity

    Args:
        query: The original search query.
        results: List of search result dicts (url, title, host, image_url, description).

    Returns:
        The same results list, reordered by AI ranking.
        Falls back to original order if ranking fails.

    Note:
        This function is non-blocking and will gracefully fall back
        to the original order if AI is unavailable or errors occur.
    """
    results = _filter_valid(results)

    if not results or len(results) <= 1:
        return results

    if not is_ranking_available():
        logger.debug("AI ranking skipped: No API key configured, using image-first sorting")
        return _sort_by_image(results)

    try:
        results_to_rank, remaining = _prepare_results(results)
        prompt, user_prompt = _build_ranking_prompt(query, results_to_rank)
        ranked_results = _rank_with_ai(prompt, user_prompt, results_to_rank, remaining)
        logger.info("AI ranked %d results", len(results_to_rank))
        logger.debug('AI ranking query: "%s"', query)
        return ranked_results
    except AIPrompt.DoesNotExist:
        logger.warning("search_ranking prompt not found, using image-first sorting")
        return _sort_by_image(results)
    except (AIUnavailableError, AIResponseError, ValidationError) as e:
        logger.warning("AI ranking failed: %s, using image-first sorting", e)
        logger.debug('Failed AI ranking query: "%s"', query)
        return _sort_by_image(results)
    except Exception as e:
        logger.error(f"Unexpected error in AI ranking: {e}, using image-first sorting")
        return _sort_by_image(results)


def _apply_ranking(results: list[dict], ranking: list[int]) -> list[dict]:
    """Apply the ranking indices to reorder results.

    Args:
        results: Original list of results.
        ranking: List of indices in desired order.

    Returns:
        Reordered list of results.
    """
    # Validate indices are within bounds
    valid_indices = set(range(len(results)))
    filtered_ranking = [i for i in ranking if i in valid_indices]

    # Build reordered list
    ranked = []
    seen = set()

    for idx in filtered_ranking:
        if idx not in seen:
            ranked.append(results[idx])
            seen.add(idx)

    # Append any results not included in ranking (shouldn't happen, but safety)
    for i, result in enumerate(results):
        if i not in seen:
            ranked.append(result)

    return ranked
