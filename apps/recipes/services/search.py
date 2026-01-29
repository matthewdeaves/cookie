"""
Async multi-site recipe search service.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus, urljoin, urlparse

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from curl_cffi.requests import AsyncSession
from django.utils import timezone

from apps.recipes.services.fingerprint import (
    BROWSER_PROFILES,
    get_random_delay,
)

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result from a recipe site."""
    url: str
    title: str
    host: str
    image_url: str = ''
    description: str = ''
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
        get_sources = sync_to_async(lambda: list(
            SearchSource.objects.filter(is_enabled=True)
        ))
        enabled_sources = await get_sources()

        # Filter by requested sources if specified
        if sources:
            enabled_sources = [s for s in enabled_sources if s.host in sources]

        if not enabled_sources:
            return {
                'results': [],
                'total': 0,
                'page': page,
                'has_more': False,
                'sites': {},
            }

        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.MAX_CONCURRENT)

        # Search all sources concurrently with primary browser profile
        # If all sources fail, we try fallback profiles
        primary_profile = BROWSER_PROFILES[0]

        async with AsyncSession(impersonate=primary_profile) as session:
            tasks = [
                self._search_source(session, semaphore, source, query)
                for source in enabled_sources
            ]
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
                'url': r.url,
                'title': r.title,
                'host': r.host,
                'image_url': r.image_url,
                'description': r.description,
                'rating_count': r.rating_count,
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
            'results': paginated,
            'total': total,
            'page': page,
            'has_more': end < total,
            'sites': site_counts,
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
            logger.warning(f'AI ranking failed: {e}')
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
            # Add randomized delay to avoid predictable request patterns
            await asyncio.sleep(get_random_delay())
            # Build search URL
            search_url = source.search_url_template.replace(
                '{query}',
                quote_plus(query)
            )

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
        soup = BeautifulSoup(html, 'html.parser')
        results = []

        # Try site-specific selector first
        if selector:
            elements = soup.select(selector)
            if elements:
                for el in elements[:20]:  # Limit per site
                    result = self._extract_result_from_element(el, host, base_url)
                    if result:
                        results.append(result)
                return results

        # Fallback: Look for common recipe link patterns
        results = self._fallback_parse(soup, host, base_url)
        return results[:20]  # Limit per site

    def _find_link(self, element) -> Optional[tuple]:
        """Find recipe link in an HTML element.

        Returns:
            Tuple of (link_element, url) if found, None otherwise.
        """
        link = element.find('a', href=True)
        if not link:
            link = element if element.name == 'a' and element.get('href') else None
        if not link:
            return None

        url = link.get('href', '')
        if not url:
            return None

        return link, url

    def _extract_title(self, element, link) -> str:
        """Extract title from element with multiple fallback strategies.

        Tries: heading elements, link text, title/aria-label attributes.
        """
        title_el = element.find(['h2', 'h3', 'h4', '.title', '[class*="title"]'])
        if title_el:
            title = title_el.get_text(strip=True)
            if title:
                return title

        title = link.get_text(strip=True)
        if title:
            return title

        return link.get('title', '') or link.get('aria-label', '')

    def _extract_rating(self, title: str) -> tuple[str, Optional[int]]:
        """Extract and strip rating count from title.

        Handles patterns like "Recipe Name1,392Ratings".

        Returns:
            Tuple of (cleaned_title, rating_count).
        """
        rating_match = re.search(r'([\d,]+)\s*[Rr]atings?\s*$', title)
        if not rating_match:
            return title, None

        rating_str = rating_match.group(1).replace(',', '')
        try:
            rating_count = int(rating_str)
            cleaned_title = title[:rating_match.start()].strip()
            return cleaned_title, rating_count
        except ValueError:
            return title, None

    def _extract_image(self, element, base_url: str) -> str:
        """Extract image URL with multiple fallback strategies.

        Tries: src, data-src, data-lazy-src attributes.
        """
        img = element.find('img')
        if not img:
            return ''

        image_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src', '')
        if image_url:
            return urljoin(base_url, image_url)
        return ''

    def _extract_description(self, element) -> str:
        """Extract description from element."""
        desc_el = element.find(['p', '.description', '[class*="description"]'])
        if desc_el:
            return desc_el.get_text(strip=True)[:200]
        return ''

    def _extract_result_from_element(
        self,
        element,
        host: str,
        base_url: str,
    ) -> Optional[SearchResult]:
        """Extract search result data from an HTML element."""
        # Find and validate link
        link_result = self._find_link(element)
        if not link_result:
            return None
        link, url = link_result

        # Make URL absolute and validate
        url = urljoin(base_url, url)
        if not self._looks_like_recipe_url(url, host):
            return None

        # Extract title
        title = self._extract_title(element, link)
        if not title:
            return None

        # Extract and strip rating from title
        title, rating_count = self._extract_rating(title)

        # Title may have become empty after stripping rating (QA-053)
        if not title:
            return None

        return SearchResult(
            url=url,
            title=title[:200],
            host=host,
            image_url=self._extract_image(element, base_url),
            description=self._extract_description(element),
            rating_count=rating_count,
        )

    def _fallback_parse(
        self,
        soup: BeautifulSoup,
        host: str,
        base_url: str,
    ) -> list[SearchResult]:
        """
        Fallback parser for sites without a specific selector.

        Looks for common patterns in recipe search results.
        """
        results = []

        # Strategy 1: Look for article elements with links
        for article in soup.find_all('article')[:30]:
            result = self._extract_result_from_element(article, host, base_url)
            if result:
                results.append(result)

        if results:
            return results

        # Strategy 2: Look for card-like divs
        card_selectors = [
            '[class*="recipe-card"]',
            '[class*="card"]',
            '[class*="result"]',
            '[class*="item"]',
        ]
        for selector in card_selectors:
            for card in soup.select(selector)[:30]:
                result = self._extract_result_from_element(card, host, base_url)
                if result:
                    results.append(result)
            if results:
                return results

        # Strategy 3: Look for links that look like recipe URLs
        for link in soup.find_all('a', href=True)[:100]:
            url = urljoin(base_url, link.get('href', ''))
            if self._looks_like_recipe_url(url, host):
                title = link.get_text(strip=True)
                if title and len(title) > 5:
                    results.append(SearchResult(
                        url=url,
                        title=title[:200],
                        host=host,
                    ))

        return results

    def _looks_like_recipe_url(self, url: str, host: str) -> bool:
        """
        Check if a URL looks like a recipe detail page.
        """
        parsed = urlparse(url)

        # Must be from the expected host
        if host not in parsed.netloc:
            return False

        path = parsed.path.lower()

        # Common recipe URL patterns
        recipe_patterns = [
            r'/recipe[s]?/',
            r'/dish/',
            r'/food/',
            r'/cooking/',
            r'/\d+/',  # Numeric ID in path
            r'-recipe/?$',  # URL ending with -recipe
            r'/a\d+/',  # Alphanumeric IDs like /a69912280/
            r'/food-cooking/',  # Pioneer Woman style
        ]

        # Exclude non-recipe paths
        exclude_patterns = [
            r'/search',
            r'/tag/',
            r'/category/',
            r'/author/',
            r'/profile/',
            r'/user/',
            r'/about',
            r'/contact',
            r'/privacy',
            r'/terms',
            r'/newsletter',
            r'/subscribe',
            # Article/blog paths (QA-053)
            r'/article/',
            r'/articles/',
            r'/blog/',
            r'/post/',
            r'/posts/',
            r'/news/',
            r'/story/',
            r'/stories/',
            r'/feature/',
            r'/features/',
            r'/guide/',
            r'/guides/',
            r'/review/',
            r'/reviews/',
            r'/roundup/',
            r'/list/',
            r'/listicle/',
            # Video paths (QA-053)
            r'/video/',
            r'/videos/',
            r'/watch/',
            r'/watch\?',
            r'/embed/',
            r'/player/',
            r'/clip/',
            r'/clips/',
            r'/episode/',
            r'/episodes/',
            r'/series/',
            r'/show/',
            r'/shows/',
            r'/gallery/',
            r'/galleries/',
            r'/slideshow/',
            r'/photo-gallery/',
            # Index/listing pages (QA-053)
            r'/seasons?(?:/|$)',
            r'/cuisines?(?:/|$)',
            r'/ingredients?(?:/|$)',
            r'/collections?(?:/|$)',
            r'/occasions?(?:/|$)',
            r'/courses?(?:/|$)',
            r'/diets?(?:/|$)',
            r'/techniques?(?:/|$)',
            r'/chefs?(?:/|$)',
            r'/dishes(?:/|$)',
            r'/menus?(?:/|$)',
            r'/meal-plans?(?:/|$)',
        ]

        for pattern in exclude_patterns:
            if re.search(pattern, path):
                return False

        # Site-specific requirements (QA-058)
        # AllRecipes has article pages at root that look like recipes but aren't
        # Real recipes are always under /recipe/ path
        if 'allrecipes.com' in host and '/recipe/' not in path:
            return False

        # Check for recipe patterns
        for pattern in recipe_patterns:
            if re.search(pattern, path):
                return True

        # Heuristic: URL path has enough segments and isn't too short
        segments = [s for s in path.split('/') if s]
        if len(segments) >= 2 and len(path) > 20:
            return True

        # Also accept single-segment slug-style URLs (common for food blogs)
        # e.g., /30-cloves-garlic-chicken/
        if len(segments) == 1 and len(path) > 15 and path.count('-') >= 2:
            return True

        return False

    async def _record_failure(self, source) -> None:
        """Record a search failure for maintenance tracking."""
        from apps.recipes.models import SearchSource

        @sync_to_async
        def update():
            source.consecutive_failures += 1
            if source.consecutive_failures >= 3:
                source.needs_attention = True
            source.save(update_fields=['consecutive_failures', 'needs_attention'])

        await update()

    async def _record_success(self, source) -> None:
        """Record a successful search."""
        from apps.recipes.models import SearchSource

        @sync_to_async
        def update():
            source.consecutive_failures = 0
            source.needs_attention = False
            source.last_validated_at = timezone.now()
            source.save(update_fields=[
                'consecutive_failures',
                'needs_attention',
                'last_validated_at',
            ])

        await update()
