"""
Async multi-site recipe search service.
"""

import asyncio
import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import quote_plus

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from django.utils import timezone

from apps.core.validators import (
    MAX_HTML_SIZE,
    MAX_REDIRECT_HOPS,
    check_content_size,
    check_response_size,
    validate_redirect_url,
)
from apps.recipes.services.fingerprint import (
    get_fallback_profiles,
    get_random_delay,
    get_random_profile,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from a recipe site."""

    url: str
    title: str
    host: str
    image_url: str = ""
    description: str = ""
    rating_count: Optional[int] = None


class RecipeSearch:
    """
    Async recipe search service that queries multiple sites concurrently.

    Uses curl_cffi with browser impersonation to fetch search pages,
    then parses results using BeautifulSoup with site-specific selectors.

    Browser profiles are centralized in fingerprint.py for maintainability.
    """

    MAX_CONCURRENT = 10
    DEFAULT_TIMEOUT = 30

    def __init__(self):
        self.timeout = self.DEFAULT_TIMEOUT

    async def search(
        self,
        query: str,
        sources: Optional[list[str]] = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """
        Search for recipes across multiple sites.

        Args:
            query: Search query string
            sources: Optional list of hosts to search (None = all enabled)
            page: Page number (1-indexed)
            per_page: Results per page

        Returns:
            dict with keys:
                - results: List of SearchResult dicts
                - total: Total result count
                - page: Current page
                - has_more: Whether more results exist
                - sites: Dict mapping host to result count
        """
        enabled_sources = await self._get_enabled_sources(sources)

        if not enabled_sources:
            return self._empty_response(page)

        results_by_source = await self._fetch_all_sources(enabled_sources, query)
        all_results, site_counts = await self._aggregate_results(
            enabled_sources,
            results_by_source,
        )

        result_dicts = self._deduplicate_and_convert(all_results)
        result_dicts = self._filter_relevant(query, result_dicts)
        if result_dicts:
            result_dicts = self._apply_ai_ranking(query, result_dicts)

        return self._paginate(result_dicts, page, per_page, site_counts)

    async def _get_enabled_sources(self, sources: Optional[list[str]] = None) -> list:
        """Load enabled search sources, optionally filtered by host name."""
        from apps.recipes.models import SearchSource

        get_sources = sync_to_async(lambda: list(SearchSource.objects.filter(is_enabled=True)))
        enabled = await get_sources()
        if sources:
            enabled = [s for s in enabled if s.host in sources]
        return enabled

    @staticmethod
    def _empty_response(page: int) -> dict:
        """Return an empty search response."""
        return {
            "results": [],
            "total": 0,
            "page": page,
            "has_more": False,
            "sites": {},
        }

    async def _fetch_all_sources(self, enabled_sources: list, query: str) -> list:
        """Search all sources concurrently and return raw results."""
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)
        primary_profile = get_random_profile()

        async with AsyncSession(impersonate=primary_profile) as session:
            tasks = [self._search_source(session, semaphore, source, query) for source in enabled_sources]
            return await asyncio.gather(*tasks, return_exceptions=True)

    async def _aggregate_results(
        self,
        enabled_sources: list,
        results_by_source: list,
    ) -> tuple[list["SearchResult"], dict[str, int]]:
        """Aggregate per-source results, recording successes and failures."""
        all_results: list[SearchResult] = []
        site_counts: dict[str, int] = {}

        for source, result in zip(enabled_sources, results_by_source):
            if isinstance(result, Exception):
                logger.warning(f"Search failed for {source.host}: {result}")
                await self._record_failure(source)
                continue

            site_counts[source.host] = len(result)
            all_results.extend(result)
            await self._record_success(source)

        return all_results, site_counts

    @staticmethod
    def _deduplicate_and_convert(results: list["SearchResult"]) -> list[dict]:
        """Deduplicate results by URL and convert to dict format for ranking."""
        seen_urls: set[str] = set()
        unique: list[dict] = []
        for r in results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique.append(
                    {
                        "url": r.url,
                        "title": r.title,
                        "host": r.host,
                        "image_url": r.image_url,
                        "description": r.description,
                        "rating_count": r.rating_count,
                    }
                )
        return unique

    @staticmethod
    def _paginate(
        result_dicts: list[dict],
        page: int,
        per_page: int,
        site_counts: dict[str, int],
    ) -> dict:
        """Paginate results and build the final response dict."""
        total = len(result_dicts)
        start = (page - 1) * per_page
        end = start + per_page
        return {
            "results": result_dicts[start:end],
            "total": total,
            "page": page,
            "has_more": end < total,
            "sites": site_counts,
        }

    @staticmethod
    def _filter_relevant(query: str, results: list[dict]) -> list[dict]:
        """Filter results to those where at least one query term appears in the title.

        This prevents nonsensical queries (e.g., "xyznonexistent") from returning
        unrelated results that happen to be scraped from source search pages.
        """
        query_terms = [t.lower() for t in query.split() if len(t) >= 2]
        if not query_terms:
            return results

        filtered = []
        for result in results:
            title_lower = result["title"].lower()
            if any(term in title_lower for term in query_terms):
                filtered.append(result)
        return filtered

    @staticmethod
    def _apply_ai_ranking(query: str, results: list[dict]) -> list[dict]:
        """Rank search results by relevance using deterministic scoring."""
        from apps.ai.services.ranking import rank_results

        return rank_results(query, results)

    async def _search_source(
        self,
        session: AsyncSession,
        semaphore: asyncio.Semaphore,
        source,
        query: str,
    ) -> list[SearchResult]:
        """
        Search a single source for recipes.

        Uses randomized delays and retry with fallback browser profiles
        to avoid bot detection patterns.
        """
        async with semaphore:
            await asyncio.sleep(get_random_delay())
            search_url = source.search_url_template.replace("{query}", quote_plus(query))
            profiles_to_try = self._build_profile_list(session)

            last_error = None
            for i, profile in enumerate(profiles_to_try[:3]):
                if i > 0:
                    await asyncio.sleep(get_random_delay() * (i + 1))
                result, error = await self._try_fetch_and_parse(
                    session,
                    search_url,
                    profile,
                    source,
                )
                if result is not None:
                    return result
                last_error = error or last_error

            raise last_error or Exception("All retry attempts failed")

    async def _try_fetch_and_parse(self, session, url, profile, source):
        """Attempt a single fetch+parse. Returns (results, None) or (None, error)."""
        try:
            response = await self._fetch_with_profile(session, url, profile)
            if response.status_code == 200:
                return self._parse_search_results(
                    response.text,
                    source.host,
                    source.result_selector,
                    url,
                ), None
            error = Exception(f"HTTP {response.status_code}")
            if not self._should_retry_status(response.status_code):
                raise error
            return None, error
        except asyncio.TimeoutError:
            return None, Exception("Request timed out")
        except Exception as e:
            if not self._should_retry_error(e):
                raise
            return None, e

    @staticmethod
    def _build_profile_list(session):
        """Build ordered list of browser profiles to try."""
        current = session._impersonate if hasattr(session, "_impersonate") else None
        profiles = [None]  # None = use session's existing profile
        profiles.extend(get_fallback_profiles(exclude=current))
        return profiles

    async def _fetch_with_profile(self, session: AsyncSession, url: str, profile):
        """Fetch a URL, using a new session with the given profile or the existing session."""
        if profile:
            async with AsyncSession(impersonate=profile) as retry_session:
                return await self._fetch_url(retry_session, url)
        return await self._fetch_url(session, url)

    @staticmethod
    def _should_retry_status(status_code: int) -> bool:
        """Return True if the HTTP status code is transient and worth retrying."""
        return status_code in (403, 404, 429) or status_code >= 500

    @staticmethod
    def _should_retry_error(error: Exception) -> bool:
        """Return True if the exception represents a transient error worth retrying."""
        error_str = str(error)
        if "HTTP" not in error_str:
            return True
        return any(code in error_str for code in ("403", "404", "429", "500", "502", "503"))

    async def _fetch_url(self, session: AsyncSession, url: str):
        """Fetch a URL with timeout handling, redirect validation, and size limits."""
        current_url = url
        current_resolve = []
        for _ in range(MAX_REDIRECT_HOPS):
            response = await asyncio.wait_for(
                session.get(current_url, timeout=self.timeout, allow_redirects=False, resolve=current_resolve),
                timeout=self.timeout + 5,
            )

            if response.status_code in (301, 302, 303, 307, 308):
                location = response.headers.get("location")
                if not location:
                    return response
                resolved = validate_redirect_url(location)
                current_url = location
                current_resolve = resolved.curl_resolve
                continue

            if response.status_code == 200:
                if not check_response_size(response, MAX_HTML_SIZE):
                    raise ValueError(f"Search response too large for {url}")
                check_content_size(response.content, MAX_HTML_SIZE)

            return response

        raise ValueError(f"Too many redirects (>{MAX_REDIRECT_HOPS}) for {url}")

    def _parse_search_results(
        self,
        html: str,
        host: str,
        selector: str,
        base_url: str,
    ) -> list[SearchResult]:
        """
        Parse search results from HTML.

        Uses the site-specific CSS selector if available,
        otherwise falls back to common patterns.
        """
        from apps.recipes.services.search_parsers import (
            extract_result_from_element,
            fallback_parse,
        )

        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Try site-specific selector first
        if selector:
            elements = soup.select(selector)
            if elements:
                for el in elements[:20]:  # Limit per site
                    result = extract_result_from_element(el, host, base_url)
                    if result:
                        results.append(result)
                return results

        # Fallback: Look for common recipe link patterns
        results = fallback_parse(soup, host, base_url)
        return results[:20]  # Limit per site

    async def _record_failure(self, source) -> None:
        """Record a search failure for maintenance tracking."""

        @sync_to_async
        def update():
            source.consecutive_failures += 1
            if source.consecutive_failures >= 2:
                source.needs_attention = True
            source.save(update_fields=["consecutive_failures", "needs_attention"])

        await update()

    async def _record_success(self, source) -> None:
        """Record a successful search."""

        @sync_to_async
        def update():
            source.consecutive_failures = 0
            source.needs_attention = False
            source.last_validated_at = timezone.now()
            source.save(
                update_fields=[
                    "consecutive_failures",
                    "needs_attention",
                    "last_validated_at",
                ]
            )

        await update()
