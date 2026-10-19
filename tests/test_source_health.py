"""Tests for apps.recipes.services.source_health: the interface is the test surface."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asgiref.sync import sync_to_async

from apps.recipes.models import SearchSource
from apps.recipes.services import source_health
from apps.recipes.services.search import RecipeSearch, SearchResult


def _make(host="h.example.com", enabled=True, failures=0):
    return SearchSource.objects.create(
        host=host,
        name=host,
        search_url_template=f"https://{host}/s?q={{query}}",
        result_selector=".r",
        is_enabled=enabled,
        consecutive_failures=failures,
    )


def _reload(pk):
    return SearchSource.objects.get(pk=pk)


@pytest.mark.django_db
class TestRecordOutcome:
    def test_threshold_is_three(self):
        assert source_health.FAILURE_THRESHOLD == 3

    def test_flags_only_at_the_threshold(self):
        src = _make()
        flags = []
        for _ in range(source_health.FAILURE_THRESHOLD):
            source_health.record_outcome(src, False)
            flags.append(_reload(src.pk).needs_attention)
        assert flags == [False, False, True]
        assert _reload(src.pk).consecutive_failures == 3

    def test_success_resets_and_stamps(self):
        src = _make(failures=5)
        src.needs_attention = True
        source_health.record_outcome(src, True)
        fresh = _reload(src.pk)
        assert (fresh.consecutive_failures, fresh.needs_attention) == (0, False)
        assert fresh.last_validated_at is not None

    def test_failure_stamps_only_when_asked(self):
        src = _make()
        source_health.record_outcome(src, False)
        assert _reload(src.pk).last_validated_at is None
        source_health.record_outcome(src, False, stamp_on_failure=True)
        assert _reload(src.pk).last_validated_at is not None

    def test_only_health_fields_are_written(self):
        src = _make()
        SearchSource.objects.filter(pk=src.pk).update(result_selector=".changed")
        source_health.record_outcome(src, False)
        assert _reload(src.pk).result_selector == ".changed"


def _fake_search(response=None, exc=None):
    search = MagicMock()
    search.search = AsyncMock(return_value=response, side_effect=exc)
    return search


@pytest.mark.django_db(transaction=True)
class TestRunCheck:
    async def test_results_are_success(self):
        src = await sync_to_async(_make)(failures=2)
        search = _fake_search({"results": [{"title": "Chicken Soup"}]})
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=search):
            result = await source_health.run_check(src)
        assert (result.ok, result.results_count, result.titles, result.error) == (True, 1, ["Chicken Soup"], None)
        assert search.search.await_args.kwargs["record_health"] is False
        assert search.search.await_args.kwargs["query"] == "chicken"
        fresh = await sync_to_async(_reload)(src.pk)
        assert fresh.consecutive_failures == 0

    async def test_zero_results_is_one_failure(self):
        src = await sync_to_async(_make)()
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=_fake_search({"results": []})):
            result = await source_health.run_check(src)
        assert result.ok is False
        fresh = await sync_to_async(_reload)(src.pk)
        assert fresh.consecutive_failures == 1
        assert fresh.last_validated_at is not None

    async def test_exception_is_one_failure_and_does_not_raise(self):
        src = await sync_to_async(_make)()
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=_fake_search(exc=OSError("boom"))):
            result = await source_health.run_check(src)
        assert (result.ok, result.error) == (False, "boom")
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 1

    async def test_real_search_with_empty_page_counts_once(self):
        """The search must not record on top of the check (the old double count)."""
        src = await sync_to_async(_make)()
        with patch.object(RecipeSearch, "_search_source", AsyncMock(return_value=[])):
            result = await source_health.run_check(src)
        assert result.ok is False
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 1

    async def test_real_search_with_failing_source_counts_once(self):
        src = await sync_to_async(_make)()
        with patch.object(RecipeSearch, "_search_source", AsyncMock(side_effect=Exception("HTTP 403"))):
            result = await source_health.run_check(src)
        assert result.ok is False
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 1


@pytest.mark.django_db(transaction=True)
class TestSearchReportsThroughSourceHealth:
    async def test_search_records_by_default(self):
        src = await sync_to_async(_make)()
        with patch.object(RecipeSearch, "_search_source", AsyncMock(side_effect=Exception("HTTP 403"))):
            await RecipeSearch().search("cookies", sources=[src.host])
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 1

    async def test_search_success_with_results_resets(self):
        src = await sync_to_async(_make)(failures=2)
        hit = [SearchResult(url=f"https://{src.host}/r/1", title="Cookies", host=src.host)]
        with patch.object(RecipeSearch, "_search_source", AsyncMock(return_value=hit)):
            await RecipeSearch().search("cookies", sources=[src.host])
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 0

    async def test_record_health_false_records_nothing(self):
        src = await sync_to_async(_make)()
        with patch.object(RecipeSearch, "_search_source", AsyncMock(side_effect=Exception("HTTP 403"))):
            await RecipeSearch().search("cookies", sources=[src.host], record_health=False)
        assert (await sync_to_async(_reload)(src.pk)).consecutive_failures == 0


@pytest.mark.django_db(transaction=True)
class TestCliAdapters:
    async def test_check_source_dict_shape(self):
        src = await sync_to_async(_make)()
        search = _fake_search({"results": [{"title": "x"}, {"title": "y"}]})
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=search):
            out = await source_health.check_source(src)
        assert out == {
            "source_id": src.id,
            "name": src.name,
            "host": src.host,
            "ok": True,
            "status_code": 200,
            "message": 'Found 2 results for "chicken"',
            "results_count": 2,
        }

    async def test_check_source_failure_messages(self):
        src = await sync_to_async(_make)()
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=_fake_search({"results": []})):
            empty = await source_health.check_source(src)
        assert empty["ok"] is False and "selector may need updating" in empty["message"]
        assert empty["status_code"] == 200
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=_fake_search(exc=OSError("x"))):
            err = await source_health.check_source(src)
        assert err["message"] == "Test failed: x" and err["status_code"] is None

    async def test_check_all_only_checks_enabled_sources(self):
        on = await sync_to_async(_make)("on.example.com")
        await sync_to_async(_make)("off.example.com", enabled=False)
        with patch("apps.recipes.services.source_health.RecipeSearch", return_value=_fake_search({"results": []})):
            results = await source_health.check_all_sources()
        assert [r["source_id"] for r in results] == [on.id]


@pytest.mark.django_db
def test_sources_api_exposes_the_threshold(client):
    from apps.profiles.models import Profile

    profile = Profile.objects.create(name="P", avatar_color="#fff")
    _make()
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    data = client.get("/api/sources/").json()
    assert data[0]["failure_threshold"] == source_health.FAILURE_THRESHOLD


@pytest.mark.django_db(transaction=True)
async def test_test_all_endpoint_function_summarises_checks():
    """The router auth wrapper is bypassed by calling the handler directly (AsyncClient 405s here)."""
    from apps.recipes.sources_api import test_all_sources

    good = await sync_to_async(_make)("good.example.com")
    bad = await sync_to_async(_make)("bad.example.com")

    async def fake_search(query, sources, page, per_page, record_health):
        if sources == [good.host]:
            return {"results": [{"title": "Chicken"}]}
        raise OSError("down")

    search = MagicMock()
    search.search = fake_search
    with patch("apps.recipes.services.source_health.RecipeSearch", return_value=search):
        out = await test_all_sources(MagicMock())

    assert (out["tested"], out["passed"], out["failed"]) == (2, 1, 1)
    by_host = {d["host"]: d for d in out["details"]}
    assert by_host[good.host]["success"] is True and by_host[good.host]["results_count"] == 1
    assert by_host[bad.host] == {"id": bad.id, "name": bad.name, "host": bad.host, "success": False, "error": "down"}
    assert (await sync_to_async(_reload)(bad.pk)).consecutive_failures == 1
