"""Shared source-health-check helpers used by both the HTTP handlers and the CLI.

- `check_source(source)` runs a single source through a sample query and
  returns `{source_id, name, host, ok, status_code, message, results_count}`.
- `check_all_sources()` iterates every enabled source and returns a list of
  the same shape.

Factored out of `apps/recipes/sources_api.py` so `python manage.py cookie_admin
sources test [--id|--all]` can reuse the exact same logic as the web endpoints.
"""

from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.recipes.models import SearchSource
from apps.recipes.services.search import RecipeSearch

TEST_QUERY = "chicken"


async def check_source(source: SearchSource) -> dict[str, Any]:
    """Run the sample query against one source; update its health metadata in DB.

    Returns a plain dict safe to serialise to JSON or print.
    """
    search = RecipeSearch()
    try:
        results = await search.search(
            query=TEST_QUERY,
            sources=[source.host],
            page=1,
            per_page=3,
        )
        result_count = len(results.get("results", []))
        ok = result_count > 0

        if ok:
            source.consecutive_failures = 0
            source.needs_attention = False
        else:
            source.consecutive_failures += 1
            source.needs_attention = source.consecutive_failures >= 3
        source.last_validated_at = timezone.now()
        await sync_to_async(source.save)()

        message = (
            f'Found {result_count} results for "{TEST_QUERY}"'
            if ok
            else f'No results for "{TEST_QUERY}" — selector may need updating'
        )
        return {
            "source_id": source.id,
            "name": source.name,
            "host": source.host,
            "ok": ok,
            "status_code": 200,
            "message": message,
            "results_count": result_count,
        }
    except Exception as exc:
        source.consecutive_failures += 1
        source.needs_attention = source.consecutive_failures >= 3
        source.last_validated_at = timezone.now()
        await sync_to_async(source.save)()
        return {
            "source_id": source.id,
            "name": source.name,
            "host": source.host,
            "ok": False,
            "status_code": None,
            "message": f"Test failed: {exc}",
            "results_count": 0,
        }


async def check_all_sources() -> list[dict[str, Any]]:
    """Test every enabled source sequentially and return per-source results."""
    sources = await sync_to_async(list)(SearchSource.objects.filter(is_enabled=True))
    results = []
    for source in sources:
        results.append(await check_source(source))
    return results
