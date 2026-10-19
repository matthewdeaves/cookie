"""Source health: the single owner of "did this search source work?".

Interface (the test surface):
    * ``FAILURE_THRESHOLD``      - consecutive failures before a source needs attention.
    * ``record_outcome(source, ok)`` / ``arecord_outcome`` - the one place the
      "failed -> count -> flag past the threshold" rule lives.
    * ``run_check(source)``      - the one "test this source with a sample query" operation;
      records exactly one outcome and never raises.
    * ``check_source`` / ``check_all_sources`` - JSON-friendly adapters for the CLI.

``RecipeSearch`` reports per-source outcomes through ``record_outcome``; the check
operation tells it not to (``record_health=False``) so a test run is counted once,
not once by the search and again by the check.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from asgiref.sync import sync_to_async
from django.utils import timezone

from apps.recipes.models import SearchSource
from apps.recipes.services.search import RecipeSearch

TEST_QUERY = "chicken"
FAILURE_THRESHOLD = 3


def record_outcome(source: SearchSource, ok: bool, *, stamp_on_failure: bool = False) -> None:
    """Record one success/failure for ``source`` and persist the health fields.

    A success resets the counter. A failure increments it and flags the source once it
    reaches ``FAILURE_THRESHOLD``. ``last_validated_at`` is stamped on success, and on
    failure only when ``stamp_on_failure`` (an explicit check, not an ordinary search).
    """
    fields = ["consecutive_failures", "needs_attention"]
    if ok:
        source.consecutive_failures = 0
        source.needs_attention = False
    else:
        source.consecutive_failures += 1
        source.needs_attention = source.consecutive_failures >= FAILURE_THRESHOLD
    if ok or stamp_on_failure:
        source.last_validated_at = timezone.now()
        fields.append("last_validated_at")
    source.save(update_fields=fields)


arecord_outcome = sync_to_async(record_outcome)


@dataclass
class CheckResult:
    """Outcome of one ``run_check``. ``error`` is set only when the search itself raised."""

    source: SearchSource
    ok: bool
    results_count: int = 0
    titles: list[str] = field(default_factory=list)
    error: str | None = None


async def run_check(source: SearchSource, per_page: int = 3) -> CheckResult:
    """Search ``source`` for ``TEST_QUERY``, record the outcome once, and report it.

    Zero results (a 200 page that parsed to nothing) and a raised error are both
    failures; each is recorded exactly once.
    """
    try:
        response = await RecipeSearch().search(
            query=TEST_QUERY,
            sources=[source.host],
            page=1,
            per_page=per_page,
            record_health=False,
        )
    except Exception as exc:
        await arecord_outcome(source, False, stamp_on_failure=True)
        return CheckResult(source=source, ok=False, error=str(exc))

    results = response.get("results", [])
    ok = len(results) > 0
    await arecord_outcome(source, ok, stamp_on_failure=True)
    return CheckResult(source=source, ok=ok, results_count=len(results), titles=[r.get("title", "") for r in results])


async def check_source(source: SearchSource) -> dict[str, Any]:
    """CLI adapter: ``run_check`` rendered as a plain JSON-safe dict."""
    result = await run_check(source)
    if result.error is not None:
        message = f"Test failed: {result.error}"
    elif result.ok:
        message = f'Found {result.results_count} results for "{TEST_QUERY}"'
    else:
        message = f'No results for "{TEST_QUERY}" — selector may need updating'
    return {
        "source_id": source.id,
        "name": source.name,
        "host": source.host,
        "ok": result.ok,
        "status_code": None if result.error is not None else 200,
        "message": message,
        "results_count": result.results_count,
    }


async def check_all_sources() -> list[dict[str, Any]]:
    """Test every enabled source sequentially and return per-source results."""
    sources = await sync_to_async(list)(SearchSource.objects.filter(is_enabled=True))
    return [await check_source(source) for source in sources]
