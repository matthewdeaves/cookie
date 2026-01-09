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
    if not results or len(results) <= 1:
        return results

    # Check if ranking is available
    if not is_ranking_available():
        logger.debug('AI ranking skipped: No API key configured')
        return results

    try:
        prompt = AIPrompt.get_prompt('search_ranking')
    except AIPrompt.DoesNotExist:
        logger.warning('search_ranking prompt not found')
        return results

    # Format results for the AI
    # Limit to first 20 results to keep prompt size manageable
    results_to_rank = results[:20]
    remaining = results[20:] if len(results) > 20 else []

    results_text = '\n'.join(
        f'{i}. "{r.get("title", "Unknown")}" from {r.get("host", "unknown")} '
        f'- {r.get("description", "No description")[:100]}'
        f'{" [has image]" if r.get("image_url") else ""}'
        for i, r in enumerate(results_to_rank)
    )

    user_prompt = prompt.format_user_prompt(
        query=query,
        results=results_text,
        count=len(results_to_rank),
    )

    try:
        service = OpenRouterService()
        response = service.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            model=prompt.model,
            json_response=True,
        )

        # Validate response - expects array of integers (indices)
        validator = AIResponseValidator()
        ranking = validator.validate('search_ranking', response)

        # Apply ranking
        ranked_results = _apply_ranking(results_to_rank, ranking)

        # Append any remaining results that weren't ranked
        ranked_results.extend(remaining)

        logger.info(f'AI ranked {len(results_to_rank)} results for query "{query}"')
        return ranked_results

    except (AIUnavailableError, AIResponseError, ValidationError) as e:
        logger.warning(f'AI ranking failed for query "{query}": {e}')
        return results
    except Exception as e:
        logger.error(f'Unexpected error in AI ranking: {e}')
        return results


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
