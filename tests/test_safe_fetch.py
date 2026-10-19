"""Tests for apps.core.safe_fetch: the interface is the test surface.

A fake ``session_factory`` scripts the responses, so the redirect/pinning/size rules are
verified without a network or curl_cffi sessions. DNS is faked per hostname.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from curl_cffi import CurlOpt

from apps.core.safe_fetch import (
    Fetched,
    RedirectLimitExceeded,
    ResponseTooLarge,
    safe_fetch,
)
from apps.core.validators import MAX_REDIRECT_HOPS

IPS = {
    "example.com": "93.184.216.34",
    "cdn.example.net": "151.101.1.1",
    "internal.example.com": "10.0.0.5",
    "meta.example.com": "169.254.169.254",
    "loop.example.com": "127.0.0.1",
}


def _dns(hostname):
    if hostname not in IPS:
        raise ValueError(f"Could not resolve hostname: {hostname}")
    return IPS[hostname]


@pytest.fixture(autouse=True)
def fake_dns():
    with patch("apps.core.validators.resolve_hostname", side_effect=_dns) as resolver:
        yield resolver


def resp(status=200, headers=None, content=b"ok", text="ok", chunks=None):
    r = MagicMock()
    r.status_code = status
    r.headers = headers or {}
    r.content = content
    r.text = text
    r.quit_now = MagicMock()
    r.aclose = AsyncMock()
    r.chunks_read = 0
    parts = chunks if chunks is not None else [content]

    async def aiter_content():
        for part in parts:
            r.chunks_read += 1
            yield part

    r.aiter_content = aiter_content
    return r


def redirect(location, status=302):
    return resp(status, {"location": location} if location else {})


class FakeSessions:
    """Callable standing in for AsyncSession; hands out scripted responses in order."""

    def __init__(self, *responses, delay=0):
        self.responses = list(responses)
        self.sessions = []  # (impersonate, curl_options)
        self.gets = []  # (url, kwargs)
        self.delay = delay

    def __call__(self, impersonate=None, curl_options=None):
        self.sessions.append((impersonate, curl_options))
        outer = self

        class _Session:
            async def __aenter__(self_inner):
                return self_inner

            async def __aexit__(self_inner, *exc):
                return None

            async def get(self_inner, url, **kwargs):
                outer.gets.append((url, kwargs))
                if outer.delay:
                    await asyncio.sleep(outer.delay)
                return outer.responses.pop(0) if len(outer.responses) > 1 else outer.responses[0]

        return _Session()


async def fetch(factory, url="https://example.com/page", **kw):
    kw.setdefault("impersonate", "chrome")
    kw.setdefault("timeout", 5)
    return await safe_fetch(url, session_factory=factory, **kw)


def pin(host, port=443):
    return {CurlOpt.RESOLVE: [f"{host}:{port}:{IPS[host]}"]}


class TestFirstHop:
    async def test_is_validated_and_pinned(self):
        factory = FakeSessions(resp())
        result = await fetch(factory)
        assert isinstance(result, Fetched)
        assert result.url == "https://example.com/page"
        assert factory.sessions == [("chrome", pin("example.com"))]
        assert factory.gets[0][1] == {"timeout": 5, "allow_redirects": False}

    @pytest.mark.parametrize("host", ["internal.example.com", "meta.example.com", "loop.example.com"])
    async def test_private_target_is_refused_before_any_request(self, host):
        factory = FakeSessions(resp())
        with pytest.raises(ValueError, match="blocked IP"):
            await fetch(factory, f"https://{host}/x")
        assert factory.sessions == []

    async def test_bad_scheme_and_unresolvable_host_are_refused(self):
        factory = FakeSessions(resp())
        with pytest.raises(ValueError, match="scheme"):
            await fetch(factory, "file:///etc/passwd")
        with pytest.raises(ValueError, match="resolve"):
            await fetch(factory, "https://nope.invalid/x")
        assert factory.sessions == []

    async def test_caller_supplied_pin_skips_revalidation(self, fake_dns):
        factory = FakeSessions(resp())
        await fetch(factory, curl_resolve=["example.com:443:93.184.216.34"])
        fake_dns.assert_not_called()
        assert factory.sessions[0][1] == {CurlOpt.RESOLVE: ["example.com:443:93.184.216.34"]}


class TestPinning:
    async def test_non_standard_port_is_pinned_on_first_hop(self):
        factory = FakeSessions(resp())
        await fetch(factory, "https://example.com:8443/x")
        assert factory.sessions == [("chrome", pin("example.com", 8443))]

    async def test_non_standard_port_is_pinned_on_redirect_hop(self):
        factory = FakeSessions(redirect("http://cdn.example.net:8080/i"), resp())
        await fetch(factory)
        assert [s[1] for s in factory.sessions] == [pin("example.com"), pin("cdn.example.net", 8080)]

    async def test_http_default_port_is_80(self):
        factory = FakeSessions(resp())
        await fetch(factory, "http://example.com/x")
        assert factory.sessions[0][1] == pin("example.com", 80)


class TestRedirects:
    async def test_each_hop_is_validated_and_pinned_to_its_own_ip(self):
        factory = FakeSessions(redirect("https://cdn.example.net/img.jpg", 301), resp(content=b"img"))
        result = await fetch(factory)
        assert result.url == "https://cdn.example.net/img.jpg"
        assert result.response.content == b"img"
        assert [s[1] for s in factory.sessions] == [pin("example.com"), pin("cdn.example.net")]
        assert all(kw["allow_redirects"] is False for _, kw in factory.gets)

    @pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
    async def test_every_redirect_status_is_followed(self, status):
        factory = FakeSessions(redirect("https://cdn.example.net/", status), resp())
        assert (await fetch(factory)).url == "https://cdn.example.net/"

    @pytest.mark.parametrize("target", ["internal.example.com", "meta.example.com", "loop.example.com"])
    async def test_redirect_to_private_ip_is_blocked_without_a_second_request(self, target):
        factory = FakeSessions(redirect(f"http://{target}/admin"), resp(content=b"secret"))
        with pytest.raises(ValueError, match="blocked IP"):
            await fetch(factory)
        assert len(factory.gets) == 1

    async def test_redirect_to_other_scheme_is_blocked(self):
        factory = FakeSessions(redirect("gopher://example.com/x"), resp())
        with pytest.raises(ValueError, match="scheme"):
            await fetch(factory)
        assert len(factory.gets) == 1

    async def test_redirect_without_location_is_returned_to_the_caller(self):
        factory = FakeSessions(redirect(None, 302))
        result = await fetch(factory)
        assert result.response.status_code == 302
        assert len(factory.gets) == 1

    async def test_hop_limit(self):
        factory = FakeSessions(redirect("https://example.com/again"))
        with pytest.raises(RedirectLimitExceeded, match="Too many redirects"):
            await fetch(factory)
        assert len(factory.gets) == MAX_REDIRECT_HOPS

    async def test_exactly_the_hop_limit_minus_one_redirects_still_succeeds(self):
        factory = FakeSessions(*[redirect("https://example.com/n")] * (MAX_REDIRECT_HOPS - 1), resp())
        assert (await fetch(factory)).response.status_code == 200


class TestSizeLimits:
    async def test_declared_content_length_over_limit(self):
        factory = FakeSessions(resp(headers={"content-length": "101"}))
        with pytest.raises(ResponseTooLarge, match="Content-Length"):
            await fetch(factory, max_size=100)

    async def test_actual_body_over_limit_without_header(self):
        factory = FakeSessions(resp(content=b"x" * 101))
        with pytest.raises(ResponseTooLarge, match="too large"):
            await fetch(factory, max_size=100)

    async def test_chunked_body_without_content_length_is_aborted_mid_stream(self):
        response = resp(chunks=[b"x" * 60] * 50)
        with pytest.raises(ResponseTooLarge, match="too large"):
            await fetch(FakeSessions(response), max_size=100)
        assert response.chunks_read == 2  # stopped as soon as the cap was passed
        response.quit_now.set.assert_called_once()

    async def test_streamed_body_is_assembled_for_the_caller(self):
        result = await fetch(FakeSessions(resp(chunks=[b"ab", b"cd"])), max_size=100)
        assert result.response.content == b"abcd"

    async def test_declared_oversize_is_refused_before_reading(self):
        response = resp(headers={"content-length": "999"}, chunks=[b"x"])
        with pytest.raises(ResponseTooLarge):
            await fetch(FakeSessions(response), max_size=100)
        assert response.chunks_read == 0

    async def test_within_limit_and_no_limit(self):
        assert (await fetch(FakeSessions(resp(content=b"x" * 100)), max_size=100)).response.status_code == 200
        assert (await fetch(FakeSessions(resp(content=b"x" * 10_000)))).response.status_code == 200

    async def test_only_200_bodies_are_checked(self):
        factory = FakeSessions(resp(status=404, content=b"x" * 1000))
        assert (await fetch(factory, max_size=100)).response.status_code == 404

    async def test_size_is_checked_on_the_final_hop_only(self):
        factory = FakeSessions(redirect("https://cdn.example.net/"), resp(content=b"x" * 101))
        with pytest.raises(ResponseTooLarge):
            await fetch(factory, max_size=100)


class TestTimeouts:
    async def test_hard_timeout_cuts_off_a_stalled_request(self):
        with pytest.raises(asyncio.TimeoutError):
            await fetch(FakeSessions(resp(), delay=1), hard_timeout=0.05)

    async def test_network_errors_propagate_unchanged(self):
        factory = FakeSessions(resp())
        factory.responses = []
        with patch.object(FakeSessions, "__call__", side_effect=OSError("down")):
            with pytest.raises(OSError):
                await fetch(factory)


class TestCallersUseTheSeam:
    """Each caller keeps its own mapping of the shared outcomes."""

    async def test_search_validates_the_first_hop(self):
        """Regression: search used to fetch its first URL without any SSRF validation."""
        from apps.recipes.services.search import RecipeSearch

        session_class = MagicMock()
        with patch("apps.recipes.services.search.AsyncSession", session_class):
            with pytest.raises(ValueError, match="blocked IP"):
                await RecipeSearch()._fetch_url(
                    MagicMock(_impersonate="chrome"), "http://internal.example.com/search?q=x"
                )
        session_class.assert_not_called()

    async def test_search_pins_the_first_hop_and_flags_oversized_pages(self):
        from apps.recipes.services.search import RecipeSearch

        factory = FakeSessions(resp(headers={"content-length": str(10**9)}))
        with patch("apps.recipes.services.search.AsyncSession", factory):
            with pytest.raises(ValueError, match="Search response too large"):
                await RecipeSearch()._fetch_url(MagicMock(_impersonate="safari"), "https://example.com/search?q=x")
        assert factory.sessions == [("safari", pin("example.com"))]

    async def test_scraper_maps_shared_outcomes_to_fetch_errors(self):
        from apps.recipes.services.scraper import FetchError, RecipeScraper

        scraper = RecipeScraper()
        url = "https://example.com/r"
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(redirect(None))):
            with pytest.raises(FetchError, match="Redirect without Location"):
                await scraper._fetch_with_redirects(url, "chrome", 100)
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(redirect("https://example.com/a"))):
            with pytest.raises(FetchError, match=r"Too many redirects \(>5\)"):
                await scraper._fetch_with_redirects(url, "chrome", 100)
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(resp(404))):
            with pytest.raises(FetchError, match="not found"):
                await scraper._fetch_with_redirects(url, "chrome", 100)
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(resp(403))):
            assert await scraper._fetch_with_redirects(url, "chrome", 100) is None
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(resp(text="<html>"))):
            assert await scraper._fetch_with_redirects(url, "chrome", 100) == "<html>"

    async def test_image_fetchers_return_none_for_every_unsafe_outcome(self):
        from apps.recipes.services.image_cache import SearchImageCache
        from apps.recipes.services.scraper import RecipeScraper

        cache = SearchImageCache()
        scraper = RecipeScraper()
        url = "https://example.com/a.jpg"
        unsafe = [
            FakeSessions(redirect("http://internal.example.com/a.jpg")),
            FakeSessions(redirect(None)),
            FakeSessions(redirect("https://example.com/loop.jpg")),
            FakeSessions(resp(headers={"content-type": "image/jpeg", "content-length": str(10**12)})),
            FakeSessions(resp(404)),
        ]
        for factory in unsafe:
            with patch("apps.recipes.services.image_cache.AsyncSession", factory):
                assert await cache._fetch_image_safe(url, "chrome") is None
        for factory in unsafe:
            with patch("apps.recipes.services.scraper.AsyncSession", factory):
                assert await scraper._fetch_image_with_redirects(url, "chrome") is None

    async def test_image_fetchers_return_bytes_for_a_good_image(self):
        from apps.recipes.services.image_cache import SearchImageCache
        from apps.recipes.services.scraper import RecipeScraper

        good = resp(headers={"content-type": "image/jpeg"}, content=b"\xff\xd8\xff")
        with patch("apps.recipes.services.image_cache.AsyncSession", FakeSessions(good)):
            assert await SearchImageCache()._fetch_image_safe("https://example.com/a", "chrome") == b"\xff\xd8\xff"
        with patch("apps.recipes.services.scraper.AsyncSession", FakeSessions(good)):
            assert (
                await RecipeScraper()._fetch_image_with_redirects("https://example.com/a", "chrome") == b"\xff\xd8\xff"
            )
