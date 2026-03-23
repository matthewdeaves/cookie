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

from apps.recipes.services.fingerprint import BROWSER_PROFILES

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
        from apps.recipes.models import SearchSource

        # Get enabled sources
        get_sources = sync_to_async(lambda: list(SearchSource.objects.filter(is_enabled=True)))
        enabled_sources = await get_sources()

        # Filter by requested sources if specified
        if sources:
            enabled_sources = [s for s in enabled_sources if s.host in sources]

        if not enabled_sources:
            return {
                "results": [],
                "total": 0,
                "page": page,
                "has_more": False,
                "sites": {},
            }

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        # Search all sources concurrently with primary browser profile
        # If all sources fail, we try fallback profiles
        primary_profile = BROWSER_PROFILES[0]

        async with AsyncSession(impersonate=primary_profile) as session:
            tasks = [self._search_source(session, semaphore, source, query) for source in enabled_sources]
            results_by_source = await asyncio.gather(*tasks, return_exceptions=True)

        # Aggregate results
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

        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique_results.append(r)

        # Convert to dict format for ranking
        result_dicts = [
            {
                "url": r.url,
                "title": r.title,
                "host": r.host,
                "image_url": r.image_url,
                "description": r.description,
                "rating_count": r.rating_count,
            }
            for r in unique_results
        ]

        # Apply AI ranking (optional, skips if unavailable)
        result_dicts = await self._apply_ai_ranking(query, result_dicts)

        # Paginate
        total = len(result_dicts)
        start = (page - 1) * per_page
        end = start + per_page
        paginated = result_dicts[start:end]

        return {
            "results": paginated,
            "total": total,
            "page": page,
            "has_more": end < total,
            "sites": site_counts,
        }

    async def _apply_ai_ranking(self, query: str, results: list[dict]) -> list[dict]:
        """Apply AI ranking to search results (non-blocking).

        Skips ranking if AI is unavailable or if it fails.
        """
        try:
            from apps.ai.services.ranking import rank_results

            ranked = await sync_to_async(rank_results)(query, results)
            return ranked
        except Exception as e:
            logger.warning(f"AI ranking failed: {e}")
            return results

    async def _search_source(
        self,
        session: AsyncSession,
        semaphore: asyncio.Semaphore,
        source,
        query: str,
    ) -> list[SearchResult]:
        """
        Search a single source for recipes.

        Uses randomized delays to avoid bot detection patterns.
        """
        async with semaphore:
            # Build search URL
            search_url = source.search_url_template.replace("{query}", quote_plus(query))

            try:
                response = await asyncio.wait_for(
                    session.get(
                        search_url,
                        timeout=self.timeout,
                        allow_redirects=True,
                    ),
                    timeout=self.timeout + 5,  # Extra buffer for asyncio
                )

                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")

                return self._parse_search_results(
                    response.text,
                    source.host,
                    source.result_selector,
                    search_url,
                )

            except asyncio.TimeoutError:
                raise Exception("Request timed out")

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
        from apps.recipes.models import SearchSource

        @sync_to_async
        def update():
            source.consecutive_failures += 1
            if source.consecutive_failures >= 3:
                source.needs_attention = True
            source.save(update_fields=["consecutive_failures", "needs_attention"])

        await update()

    async def _record_success(self, source) -> None:
        """Record a successful search."""
        from apps.recipes.models import SearchSource

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
