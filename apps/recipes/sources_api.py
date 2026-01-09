"""
SearchSource management API endpoints.
"""

import asyncio
from typing import List, Optional

from django.utils import timezone
from ninja import Router, Schema

from .models import SearchSource
from .services.search import RecipeSearch

router = Router(tags=['sources'])


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

@router.get('/', response=List[SourceOut])
def list_sources(request):
    """List all search sources with their status."""
    sources = SearchSource.objects.all().order_by('name')
    return list(sources)


@router.get('/enabled-count/', response={200: dict})
def enabled_count(request):
    """Get count of enabled sources vs total."""
    total = SearchSource.objects.count()
    enabled = SearchSource.objects.filter(is_enabled=True).count()
    return {
        'enabled': enabled,
        'total': total,
    }


@router.get('/{source_id}/', response={200: SourceOut, 404: ErrorOut})
def get_source(request, source_id: int):
    """Get a single search source by ID."""
    try:
        source = SearchSource.objects.get(id=source_id)
        return source
    except SearchSource.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Source {source_id} not found',
        }


@router.post('/{source_id}/toggle/', response={200: SourceToggleOut, 404: ErrorOut})
def toggle_source(request, source_id: int):
    """Toggle a source's enabled status."""
    try:
        source = SearchSource.objects.get(id=source_id)
        source.is_enabled = not source.is_enabled
        source.save()
        return {
            'id': source.id,
            'is_enabled': source.is_enabled,
        }
    except SearchSource.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Source {source_id} not found',
        }


@router.post('/bulk-toggle/', response={200: BulkToggleOut})
def bulk_toggle_sources(request, data: BulkToggleIn):
    """Enable or disable all sources at once."""
    updated = SearchSource.objects.all().update(is_enabled=data.enable)
    return {
        'updated_count': updated,
        'is_enabled': data.enable,
    }


@router.put('/{source_id}/selector/', response={200: SourceUpdateOut, 404: ErrorOut})
def update_selector(request, source_id: int, data: SourceUpdateIn):
    """Update a source's CSS selector."""
    try:
        source = SearchSource.objects.get(id=source_id)
        source.result_selector = data.result_selector
        source.save()
        return {
            'id': source.id,
            'result_selector': source.result_selector,
        }
    except SearchSource.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Source {source_id} not found',
        }


@router.post('/{source_id}/test/', response={200: SourceTestOut, 404: ErrorOut, 500: ErrorOut})
async def test_source(request, source_id: int):
    """Test a source by performing a sample search.

    Uses "chicken" as a test query and checks if results are returned.
    Updates the source's validation status based on the result.
    """
    from asgiref.sync import sync_to_async

    try:
        source = await sync_to_async(SearchSource.objects.get)(id=source_id)
    except SearchSource.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Source {source_id} not found',
        }

    # Test with a common search query
    test_query = 'chicken'
    search = RecipeSearch()

    try:
        # Search only this specific source
        results = await search.search(
            query=test_query,
            sources=[source.host],
            page=1,
            per_page=5,
        )

        result_count = len(results.get('results', []))
        sample_titles = [r.get('title', '')[:50] for r in results.get('results', [])[:3]]

        # Update source validation status
        if result_count > 0:
            source.consecutive_failures = 0
            source.needs_attention = False
            source.last_validated_at = timezone.now()
            await sync_to_async(source.save)()

            return {
                'success': True,
                'message': f'Found {result_count} results for "{test_query}"',
                'results_count': result_count,
                'sample_results': sample_titles,
            }
        else:
            source.consecutive_failures += 1
            source.needs_attention = source.consecutive_failures >= 3
            source.last_validated_at = timezone.now()
            await sync_to_async(source.save)()

            return {
                'success': False,
                'message': f'No results found for "{test_query}". The selector may need updating.',
                'results_count': 0,
                'sample_results': [],
            }

    except Exception as e:
        # Update failure count
        source.consecutive_failures += 1
        source.needs_attention = source.consecutive_failures >= 3
        source.last_validated_at = timezone.now()
        await sync_to_async(source.save)()

        return 500, {
            'error': 'test_failed',
            'message': f'Test failed: {str(e)}',
        }


@router.post('/test-all/', response={200: dict})
async def test_all_sources(request):
    """Test all enabled sources and return summary.

    This may take a while as it tests each source sequentially.
    """
    from asgiref.sync import sync_to_async

    sources = await sync_to_async(list)(
        SearchSource.objects.filter(is_enabled=True)
    )

    results = {
        'tested': 0,
        'passed': 0,
        'failed': 0,
        'details': [],
    }

    search = RecipeSearch()
    test_query = 'chicken'

    for source in sources:
        try:
            search_results = await search.search(
                query=test_query,
                sources=[source.host],
                page=1,
                per_page=3,
            )

            result_count = len(search_results.get('results', []))
            success = result_count > 0

            # Update source status
            if success:
                source.consecutive_failures = 0
                source.needs_attention = False
            else:
                source.consecutive_failures += 1
                source.needs_attention = source.consecutive_failures >= 3

            source.last_validated_at = timezone.now()
            await sync_to_async(source.save)()

            results['tested'] += 1
            if success:
                results['passed'] += 1
            else:
                results['failed'] += 1

            results['details'].append({
                'id': source.id,
                'name': source.name,
                'host': source.host,
                'success': success,
                'results_count': result_count,
            })

        except Exception as e:
            source.consecutive_failures += 1
            source.needs_attention = source.consecutive_failures >= 3
            source.last_validated_at = timezone.now()
            await sync_to_async(source.save)()

            results['tested'] += 1
            results['failed'] += 1
            results['details'].append({
                'id': source.id,
                'name': source.name,
                'host': source.host,
                'success': False,
                'error': str(e),
            })

    return results
