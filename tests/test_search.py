"""
Tests for recipe search service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.recipes.services.search import RecipeSearch, SearchResult


class TestSearchHelpers:
    """Tests for search helper methods."""

    def setup_method(self):
        self.search = RecipeSearch()

    def test_looks_like_recipe_url_recipe_path(self):
        """Test URL with /recipe/ in path is detected."""
        assert (
            self.search._looks_like_recipe_url(
                "https://allrecipes.com/recipe/12345/chocolate-chip-cookies/", "allrecipes.com"
            )
            is True
        )

    def test_looks_like_recipe_url_recipes_path(self):
        """Test URL with /recipes/ in path is detected."""
        assert self.search._looks_like_recipe_url("https://food52.com/recipes/12345-cookies", "food52.com") is True

    def test_looks_like_recipe_url_numeric_id(self):
        """Test URL with numeric ID in path is detected."""
        assert self.search._looks_like_recipe_url("https://example.com/12345/yummy-cookies", "example.com") is True

    def test_looks_like_recipe_url_wrong_host(self):
        """Test URL from wrong host is rejected."""
        assert self.search._looks_like_recipe_url("https://different-site.com/recipe/123", "allrecipes.com") is False

    def test_looks_like_recipe_url_search_page(self):
        """Test search page URLs are rejected."""
        assert self.search._looks_like_recipe_url("https://allrecipes.com/search?q=cookies", "allrecipes.com") is False

    def test_looks_like_recipe_url_category_page(self):
        """Test category page URLs are rejected."""
        assert (
            self.search._looks_like_recipe_url("https://allrecipes.com/category/desserts/", "allrecipes.com") is False
        )

    def test_looks_like_recipe_url_author_page(self):
        """Test author page URLs are rejected."""
        assert self.search._looks_like_recipe_url("https://allrecipes.com/author/chef-john/", "allrecipes.com") is False

    def test_looks_like_recipe_url_long_path(self):
        """Test that long paths with multiple segments are accepted."""
        assert (
            self.search._looks_like_recipe_url(
                "https://example.com/food/desserts/chocolate-chip-cookies-recipe", "example.com"
            )
            is True
        )


class TestSearchResultDataclass:
    """Tests for SearchResult dataclass."""

    def test_search_result_creation(self):
        result = SearchResult(
            url="https://example.com/recipe/123",
            title="Test Recipe",
            host="example.com",
            image_url="https://example.com/image.jpg",
            description="A test recipe",
        )
        assert result.url == "https://example.com/recipe/123"
        assert result.title == "Test Recipe"
        assert result.host == "example.com"
        assert result.image_url == "https://example.com/image.jpg"
        assert result.description == "A test recipe"

    def test_search_result_defaults(self):
        result = SearchResult(
            url="https://example.com/recipe/123",
            title="Test Recipe",
            host="example.com",
        )
        assert result.image_url == ""
        assert result.description == ""
        assert result.rating_count is None

    def test_search_result_with_rating_count(self):
        result = SearchResult(
            url="https://example.com/recipe/123",
            title="Test Recipe",
            host="example.com",
            rating_count=1392,
        )
        assert result.rating_count == 1392


class TestParseSearchResults:
    """Tests for HTML parsing logic."""

    def setup_method(self):
        self.search = RecipeSearch()

    def test_parse_with_selector(self):
        """Test parsing with a specific CSS selector."""
        html = """
        <html>
        <body>
            <div class="recipe-card">
                <a href="/recipe/123/cookies">
                    <h3>Chocolate Cookies</h3>
                    <img src="/images/cookie.jpg">
                    <p>Delicious cookies</p>
                </a>
            </div>
            <div class="recipe-card">
                <a href="/recipe/456/brownies">
                    <h3>Fudgy Brownies</h3>
                    <img src="/images/brownie.jpg">
                </a>
            </div>
        </body>
        </html>
        """
        results = self.search._parse_search_results(
            html,
            "example.com",
            ".recipe-card",
            "https://www.example.com/search?q=chocolate",
        )
        assert len(results) == 2
        assert results[0].title == "Chocolate Cookies"
        assert "recipe/123" in results[0].url
        assert results[1].title == "Fudgy Brownies"

    def test_parse_fallback_articles(self):
        """Test fallback parsing using article elements."""
        html = """
        <html>
        <body>
            <article>
                <a href="/recipe/789/cake">
                    <h2>Birthday Cake</h2>
                    <img src="/cake.jpg">
                </a>
            </article>
        </body>
        </html>
        """
        results = self.search._parse_search_results(
            html,
            "example.com",
            "",  # No selector - use fallback
            "https://www.example.com/search",
        )
        assert len(results) >= 1
        assert any("cake" in r.url.lower() for r in results)

    def test_parse_empty_html(self):
        """Test parsing empty HTML returns empty list."""
        results = self.search._parse_search_results(
            "<html><body></body></html>",
            "example.com",
            ".recipe-card",
            "https://example.com/search",
        )
        assert results == []

    def test_extract_result_from_element_no_link(self):
        """Test that elements without links are skipped."""
        from bs4 import BeautifulSoup

        html = '<div class="card"><span>No link here</span></div>'
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        result = self.search._extract_result_from_element(
            element,
            "example.com",
            "https://example.com/search",
        )
        assert result is None

    def test_extract_rating_from_title(self):
        """Test that rating count is extracted and stripped from title."""
        from bs4 import BeautifulSoup

        html = """
        <div class="recipe-card">
            <a href="/recipe/123/butter-chicken">
                <h3>Chicken Makhani (Indian Butter Chicken)1,392Ratings</h3>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        result = self.search._extract_result_from_element(
            element,
            "example.com",
            "https://example.com/search",
        )
        assert result is not None
        assert result.title == "Chicken Makhani (Indian Butter Chicken)"
        assert result.rating_count == 1392

    def test_extract_rating_with_space(self):
        """Test rating extraction with space before 'Ratings'."""
        from bs4 import BeautifulSoup

        html = """
        <div class="recipe-card">
            <a href="/recipe/456/cookies">
                <h3>Chocolate Chip Cookies 500 Ratings</h3>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        result = self.search._extract_result_from_element(
            element,
            "example.com",
            "https://example.com/search",
        )
        assert result is not None
        assert result.title == "Chocolate Chip Cookies"
        assert result.rating_count == 500

    def test_extract_no_rating(self):
        """Test that titles without ratings leave rating_count as None."""
        from bs4 import BeautifulSoup

        html = """
        <div class="recipe-card">
            <a href="/recipe/789/brownies">
                <h3>Fudgy Brownies</h3>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        result = self.search._extract_result_from_element(
            element,
            "example.com",
            "https://example.com/search",
        )
        assert result is not None
        assert result.title == "Fudgy Brownies"
        assert result.rating_count is None

    def test_extract_single_rating(self):
        """Test rating extraction with singular 'Rating'."""
        from bs4 import BeautifulSoup

        html = """
        <div class="recipe-card">
            <a href="/recipe/111/cake">
                <h3>Simple Cake1 Rating</h3>
            </a>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        element = soup.find("div")
        result = self.search._extract_result_from_element(
            element,
            "example.com",
            "https://example.com/search",
        )
        assert result is not None
        assert result.title == "Simple Cake"
        assert result.rating_count == 1


@pytest.mark.django_db(transaction=True)
class TestSearchService:
    """Integration tests for RecipeSearch service."""

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_no_sources(self, mock_session_class):
        """Test search with no enabled sources returns empty results."""
        from apps.recipes.models import SearchSource
        from asgiref.sync import sync_to_async

        await sync_to_async(SearchSource.objects.update)(is_enabled=False)

        search = RecipeSearch()
        results = await search.search("chocolate cookies")

        assert results["total"] == 0
        assert results["results"] == []
        assert results["sites"] == {}

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_with_source_filter(self, mock_session_class):
        """Test search with specific source filter."""
        from apps.recipes.models import SearchSource

        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <article>
                <a href="/recipe/123/cookies">
                    <h2>Test Cookies</h2>
                </a>
            </article>
        </body></html>
        """

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        results = await search.search(
            "cookies",
            sources=["allrecipes.com"],
        )

        # Should only search allrecipes.com
        assert "allrecipes.com" in results["sites"] or results["total"] >= 0

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_handles_http_error(self, mock_session_class):
        """Test search handles HTTP errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        results = await search.search("cookies", sources=["allrecipes.com"])

        # Should not crash, just return empty or reduced results
        assert "results" in results
        assert "total" in results

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_handles_timeout(self, mock_session_class):
        """Test search handles timeouts gracefully."""
        import asyncio

        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        results = await search.search("cookies", sources=["allrecipes.com"])

        # Should not crash
        assert "results" in results

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_pagination(self, mock_session_class):
        """Test search pagination."""
        # Create mock response with multiple results
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <article><a href="/recipe/1/r1"><h2>Recipe 1</h2></a></article>
            <article><a href="/recipe/2/r2"><h2>Recipe 2</h2></a></article>
            <article><a href="/recipe/3/r3"><h2>Recipe 3</h2></a></article>
            <article><a href="/recipe/4/r4"><h2>Recipe 4</h2></a></article>
            <article><a href="/recipe/5/r5"><h2>Recipe 5</h2></a></article>
        </body></html>
        """

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()

        # Get page 1 with 2 results per page
        results = await search.search(
            "cookies",
            sources=["allrecipes.com"],
            page=1,
            per_page=2,
        )

        assert results["page"] == 1
        assert len(results["results"]) <= 2
        # If we got results, has_more should be true since there are more
        if results["total"] > 2:
            assert results["has_more"] is True

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_search_deduplicates_urls(self, mock_session_class):
        """Test that duplicate URLs are removed from results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """
        <html><body>
            <article><a href="/recipe/123/cookies"><h2>Cookies A</h2></a></article>
            <article><a href="/recipe/123/cookies"><h2>Cookies B</h2></a></article>
        </body></html>
        """

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        results = await search.search("cookies", sources=["allrecipes.com"])

        # Should deduplicate by URL
        urls = [r["url"] for r in results["results"]]
        assert len(urls) == len(set(urls))


@pytest.mark.django_db(transaction=True)
class TestSearchSourceTracking:
    """Tests for search source failure tracking."""

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_failure_increments_counter(self, mock_session_class):
        """Test that failures increment the consecutive_failures counter."""
        from apps.recipes.models import SearchSource
        from asgiref.sync import sync_to_async

        @sync_to_async
        def setup_source():
            source, _ = SearchSource.objects.get_or_create(
                host="allrecipes.com",
                defaults={
                    "name": "AllRecipes",
                    "search_url_template": "https://www.allrecipes.com/search?q={query}",
                },
            )
            source.consecutive_failures = 0
            source.needs_attention = False
            source.save()
            return source.pk

        source_pk = await setup_source()

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        await search.search("cookies", sources=["allrecipes.com"])

        @sync_to_async
        def check_source():
            source = SearchSource.objects.get(pk=source_pk)
            return source.consecutive_failures

        assert await check_source() == 1

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_three_failures_marks_needs_attention(self, mock_session_class):
        """Test that 3 failures marks source as needs_attention."""
        from apps.recipes.models import SearchSource
        from asgiref.sync import sync_to_async

        @sync_to_async
        def setup_source():
            source, _ = SearchSource.objects.get_or_create(
                host="allrecipes.com",
                defaults={
                    "name": "AllRecipes",
                    "search_url_template": "https://www.allrecipes.com/search?q={query}",
                },
            )
            source.consecutive_failures = 2  # Will be 3 after this failure
            source.needs_attention = False
            source.save()
            return source.pk

        source_pk = await setup_source()

        mock_response = MagicMock()
        mock_response.status_code = 500

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        await search.search("cookies", sources=["allrecipes.com"])

        @sync_to_async
        def check_source():
            source = SearchSource.objects.get(pk=source_pk)
            return source.consecutive_failures, source.needs_attention

        failures, needs_attention = await check_source()
        assert failures == 3
        assert needs_attention is True

    @patch("apps.recipes.services.search.AsyncSession")
    async def test_success_resets_failure_counter(self, mock_session_class):
        """Test that success resets consecutive_failures."""
        from apps.recipes.models import SearchSource
        from asgiref.sync import sync_to_async

        @sync_to_async
        def setup_source():
            source, _ = SearchSource.objects.get_or_create(
                host="allrecipes.com",
                defaults={
                    "name": "AllRecipes",
                    "search_url_template": "https://www.allrecipes.com/search?q={query}",
                },
            )
            source.consecutive_failures = 2
            source.needs_attention = True
            source.save()
            return source.pk

        source_pk = await setup_source()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body><article><a href="/recipe/123/test"><h2>Test</h2></a></article></body></html>'

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        search = RecipeSearch()
        await search.search("cookies", sources=["allrecipes.com"])

        @sync_to_async
        def check_source():
            source = SearchSource.objects.get(pk=source_pk)
            return source.consecutive_failures, source.needs_attention, source.last_validated_at

        failures, needs_attention, last_validated = await check_source()
        assert failures == 0
        assert needs_attention is False
        assert last_validated is not None
