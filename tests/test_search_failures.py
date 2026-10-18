"""
Search failure handling: a failed search must be distinguishable from an empty one,
must not be cached for days, and slow sources must not hold the whole request.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from django.core.cache import cache

from apps.recipes.services.search import RecipeSearch, SearchResult


@pytest.fixture(autouse=True)
def _clear_search_cache():
    cache.clear()
    yield
    cache.clear()


async def _make_session():
    from asgiref.sync import sync_to_async
    from django.contrib.sessions.backends.db import SessionStore

    from apps.profiles.models import Profile

    @sync_to_async
    def setup():
        profile = Profile.objects.create(name="Search Failure User", avatar_color="#112233")
        store = SessionStore()
        store["profile_id"] = profile.id
        store.create()
        return store.session_key

    return await setup()


async def _search(query_string):
    from django.conf import settings
    from django.test import AsyncClient

    client = AsyncClient()
    client.cookies[settings.SESSION_COOKIE_NAME] = await _make_session()
    return await client.get(f"/api/recipes/search/{query_string}")


def _fake_search(results, failed, searched):
    mock_search = MagicMock()
    mock_search.search = AsyncMock(
        return_value={
            "results": results,
            "total": len(results),
            "page": 1,
            "has_more": False,
            "sites": {},
            "failed_sources": failed,
            "sources_searched": searched,
        }
    )
    return mock_search


_RESULT = {
    "url": "https://a.com/1",
    "title": "Cookies",
    "host": "a.com",
    "image_url": "",
    "description": "",
}


@pytest.mark.django_db(transaction=True)
class TestSearchApiFailureHandling:
    @patch("apps.recipes.api.RecipeSearch")
    async def test_all_sources_failed_returns_503_and_is_not_cached(self, mock_search_class):
        mock_search_class.return_value = _fake_search([], ["a.com", "b.com"], 2)

        response = await _search("?q=cookies")

        assert response.status_code == 503
        assert "recipe sites" in response.json()["detail"]

        # A second request searches live again instead of replaying a cached "empty" answer.
        await _search("?q=cookies")
        assert mock_search_class.return_value.search.await_count == 2

    @patch("apps.recipes.api.RecipeSearch")
    async def test_partial_failure_reports_failed_sources_and_caches_briefly(self, mock_search_class):
        mock_search_class.return_value = _fake_search([_RESULT], ["blocked.com"], 2)

        with patch("apps.recipes.api.cache") as mock_cache:
            mock_cache.get = MagicMock(return_value=None)
            mock_cache.set = MagicMock()
            response = await _search("?q=cookies")

        assert response.status_code == 200
        assert response.json()["failed_sources"] == ["blocked.com"]
        assert mock_cache.set.call_args[0][2] == 300

    @patch("apps.recipes.api.RecipeSearch")
    async def test_genuinely_empty_search_is_200_with_short_cache(self, mock_search_class):
        mock_search_class.return_value = _fake_search([], [], 2)

        with patch("apps.recipes.api.cache") as mock_cache:
            mock_cache.get = MagicMock(return_value=None)
            mock_cache.set = MagicMock()
            response = await _search("?q=xyzzy")

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["failed_sources"] == []
        assert mock_cache.set.call_args[0][2] == 3600

    @patch("apps.recipes.api.RecipeSearch")
    async def test_cached_pages_do_not_consume_rate_limit(self, mock_search_class):
        mock_search_class.return_value = _fake_search([_RESULT], [], 1)

        with patch("apps.recipes.api.is_ratelimited", return_value=False) as limited:
            await _search("?q=cookies")
            await _search("?q=cookies&page=2")
            await _search("?q=cookies&sources=a.com")

        assert limited.call_count == 1

    @patch("apps.recipes.api.RecipeSearch")
    async def test_page_below_one_is_clamped(self, mock_search_class):
        mock_search_class.return_value = _fake_search([_RESULT], [], 1)

        response = await _search("?q=cookies&page=-3")

        assert response.status_code == 200
        assert response.json()["results"][0]["title"] == "Cookies"


def _source(host):
    return MagicMock(host=host, search_url_template=f"https://{host}/s?q={{query}}", result_selector="")


def _patched_session():
    session_class = patch("apps.recipes.services.search.AsyncSession")
    return session_class


@pytest.mark.django_db(transaction=True)
class TestSearchServiceDeadline:
    async def test_slow_source_is_abandoned_at_the_deadline_and_reported(self):
        search = RecipeSearch()
        search.TOTAL_TIMEOUT = 0.3

        async def fake_search_source(session, semaphore, source, query):
            if source.host == "slow.com":
                await asyncio.sleep(30)
            return [SearchResult(url="https://fast.com/r/1", title="Fast Cookies", host="fast.com")]

        record_failure = AsyncMock()
        record_success = AsyncMock()
        with (
            patch.object(
                search, "_get_enabled_sources", AsyncMock(return_value=[_source("fast.com"), _source("slow.com")])
            ),
            patch.object(search, "_search_source", fake_search_source),
            patch.object(search, "_record_failure", record_failure),
            patch.object(search, "_record_success", record_success),
            _patched_session() as session_class,
        ):
            session_class.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            session_class.return_value.__aexit__ = AsyncMock(return_value=None)
            results = await search.search("cookies")

        assert results["failed_sources"] == ["slow.com"]
        assert results["sources_searched"] == 2
        assert [r["title"] for r in results["results"]] == ["Fast Cookies"]
        # A deadline overrun is not evidence that the site's selector is broken.
        record_failure.assert_not_awaited()
        record_success.assert_awaited_once()

    async def test_http_errors_are_listed_as_failed_sources(self):
        search = RecipeSearch()
        with (
            patch.object(search, "_get_enabled_sources", AsyncMock(return_value=[_source("blocked.com")])),
            patch.object(search, "_search_source", AsyncMock(side_effect=Exception("HTTP 403"))),
            patch.object(search, "_record_failure", AsyncMock()) as record_failure,
            _patched_session() as session_class,
        ):
            session_class.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            session_class.return_value.__aexit__ = AsyncMock(return_value=None)
            results = await search.search("cookies")

        assert results["failed_sources"] == ["blocked.com"]
        assert results["results"] == []
        record_failure.assert_awaited_once()

    def test_404_is_not_retried_but_403_is(self):
        assert RecipeSearch._should_retry_status(403) is True
        assert RecipeSearch._should_retry_status(404) is False


@pytest.mark.django_db(transaction=True)
class TestImageCacheBudget:
    async def test_recently_failed_images_are_not_retried(self):
        from asgiref.sync import sync_to_async

        from apps.recipes.models import CachedSearchImage
        from apps.recipes.services.image_cache import SearchImageCache

        await sync_to_async(CachedSearchImage.objects.create)(
            external_url="https://img.example/dead.jpg", status=CachedSearchImage.STATUS_FAILED
        )

        remaining = await SearchImageCache().filter_attemptable(
            ["https://img.example/dead.jpg", "https://img.example/new.jpg"]
        )

        assert remaining == ["https://img.example/new.jpg"]

    async def test_slow_image_downloads_do_not_block_the_response(self):
        from apps.recipes import api as recipes_api

        results = [{"image_url": "https://img.example/slow.jpg"}]

        async def never_finishes(self, urls):
            await asyncio.sleep(30)

        with (
            patch.object(recipes_api, "IMAGE_CACHE_BUDGET_SECONDS", 0.2),
            patch("apps.recipes.api.SearchImageCache.cache_images", never_finishes),
        ):
            await asyncio.wait_for(recipes_api._cache_and_map_images(results), timeout=5)

        assert results[0]["cached_image_url"] is None
