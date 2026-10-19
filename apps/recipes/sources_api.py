"""
SearchSource management API endpoints.
"""

from typing import List, Optional

from asgiref.sync import sync_to_async
from ninja import Router, Schema, Status

from apps.core.auth import HomeOnlyAuth, SessionAuth

from .models import SearchSource
from .services import source_health

router = Router(tags=["sources"])


# Schemas


class SourceOut(Schema):
    id: int
    host: str
    name: str
    is_enabled: bool
    search_url_template: str
    result_selector: str
    logo_url: str
    last_validated_at: Optional[str] = None
    consecutive_failures: int
    needs_attention: bool
    failure_threshold: int

    @staticmethod
    def resolve_failure_threshold(obj):
        return source_health.FAILURE_THRESHOLD

    @staticmethod
    def resolve_last_validated_at(obj):
        if obj.last_validated_at:
            return obj.last_validated_at.isoformat()
        return None


class SourceToggleOut(Schema):
    id: int
    is_enabled: bool


class SourceUpdateIn(Schema):
    result_selector: str


class SourceUpdateOut(Schema):
    id: int
    result_selector: str


class SourceTestOut(Schema):
    success: bool
    message: str
    results_count: int
    sample_results: List[str]


class ErrorOut(Schema):
    error: str
    message: str


class BulkToggleIn(Schema):
    enable: bool


class BulkToggleOut(Schema):
    updated_count: int
    is_enabled: bool


# Endpoints


@router.get("/", response=List[SourceOut], auth=SessionAuth())
def list_sources(request):
    """List all search sources with their status."""
    sources = SearchSource.objects.all().order_by("name")
    return list(sources)


@router.get("/enabled-count/", response={200: dict}, auth=SessionAuth())
def enabled_count(request):
    """Get count of enabled sources vs total."""
    total = SearchSource.objects.count()
    enabled = SearchSource.objects.filter(is_enabled=True).count()
    return {
        "enabled": enabled,
        "total": total,
    }


# Static paths registered before parametrized `/{source_id}/*` patterns so that
# Django's URL resolver doesn't shadow them with the str-typed path segment.


@router.post("/bulk-toggle/", response={200: BulkToggleOut}, auth=HomeOnlyAuth())
def bulk_toggle_sources(request, data: BulkToggleIn):
    """Enable or disable all sources at once."""
    updated = SearchSource.objects.all().update(is_enabled=data.enable)
    return {
        "updated_count": updated,
        "is_enabled": data.enable,
    }


@router.post("/test-all/", response={200: dict}, auth=HomeOnlyAuth())
async def test_all_sources(request):
    """Test all enabled sources and return summary.

    This may take a while as it tests each source sequentially.
    """
    sources = await sync_to_async(list)(SearchSource.objects.filter(is_enabled=True))

    results = {"tested": 0, "passed": 0, "failed": 0, "details": []}
    for source in sources:
        check = await source_health.run_check(source)
        detail = {"id": source.id, "name": source.name, "host": source.host, "success": check.ok}
        if check.error is not None:
            detail["error"] = check.error
        else:
            detail["results_count"] = check.results_count
        results["tested"] += 1
        results["passed" if check.ok else "failed"] += 1
        results["details"].append(detail)
    return results


@router.get("/{source_id}/", response={200: SourceOut, 404: ErrorOut}, auth=SessionAuth())
def get_source(request, source_id: int):
    """Get a single search source by ID."""
    try:
        source = SearchSource.objects.get(id=source_id)
        return source
    except SearchSource.DoesNotExist:
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Source {source_id} not found",
            },
        )


@router.post("/{source_id}/toggle/", response={200: SourceToggleOut, 404: ErrorOut}, auth=HomeOnlyAuth())
def toggle_source(request, source_id: int):
    """Toggle a source's enabled status."""
    try:
        source = SearchSource.objects.get(id=source_id)
        source.is_enabled = not source.is_enabled
        source.save()
        return {
            "id": source.id,
            "is_enabled": source.is_enabled,
        }
    except SearchSource.DoesNotExist:
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Source {source_id} not found",
            },
        )


@router.put("/{source_id}/selector/", response={200: SourceUpdateOut, 404: ErrorOut}, auth=HomeOnlyAuth())
def update_selector(request, source_id: int, data: SourceUpdateIn):
    """Update a source's CSS selector."""
    try:
        source = SearchSource.objects.get(id=source_id)
        source.result_selector = data.result_selector
        source.save()
        return {
            "id": source.id,
            "result_selector": source.result_selector,
        }
    except SearchSource.DoesNotExist:
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Source {source_id} not found",
            },
        )


@router.post("/{source_id}/test/", response={200: SourceTestOut, 404: ErrorOut, 500: ErrorOut}, auth=HomeOnlyAuth())
async def test_source(request, source_id: int):
    """Test a source by performing a sample search.

    Uses "chicken" as a test query and checks if results are returned.
    Updates the source's validation status based on the result.
    """
    try:
        source = await sync_to_async(SearchSource.objects.get)(id=source_id)
    except SearchSource.DoesNotExist:
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Source {source_id} not found",
            },
        )

    check = await source_health.run_check(source, per_page=5)
    query = source_health.TEST_QUERY

    if check.error is not None:
        return Status(500, {"error": "test_failed", "message": f"Test failed: {check.error}"})
    if check.ok:
        return {
            "success": True,
            "message": f'Found {check.results_count} results for "{query}"',
            "results_count": check.results_count,
            "sample_results": [t[:50] for t in check.titles[:3]],
        }
    return {
        "success": False,
        "message": f'No results found for "{query}". The selector may need updating.',
        "results_count": 0,
        "sample_results": [],
    }
