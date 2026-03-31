"""Deterministic search result ranking by image presence and query relevance."""


def _filter_valid(results: list[dict]) -> list[dict]:
    """Filter out results without titles (QA-053).

    Results without titles will fail to import, so they should
    never be shown to users.
    """
    return [r for r in results if r.get("title")]


def _score_result(result: dict, query_terms: list[str]) -> int:
    """Score a single result by image presence and query term matches."""
    score = 0
    if result.get("image_url"):
        score += 100

    title_lower = result.get("title", "").lower()
    for term in query_terms:
        if term in title_lower:
            score += 5

    if query_terms and " ".join(query_terms) in title_lower:
        score += 10

    return score


def rank_results(query: str, results: list[dict]) -> list[dict]:
    """Rank search results by image presence and query relevance.

    Args:
        query: The original search query.
        results: List of search result dicts.

    Returns:
        Filtered and sorted results, highest score first.
    """
    results = _filter_valid(results)
    if not results:
        return results

    query_terms = [t for t in query.lower().split() if len(t) >= 2]
    return sorted(results, key=lambda r: _score_result(r, query_terms), reverse=True)
