"""
Tests for recipe scraper service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.recipes.services.scraper import RecipeScraper, FetchError, ParseError


class TestScraperHelpers:
    """Tests for scraper helper methods."""

    def setup_method(self):
        self.scraper = RecipeScraper()

    def test_parse_time_int(self):
        assert self.scraper._parse_time(30) == 30

    def test_parse_time_float(self):
        assert self.scraper._parse_time(30.5) == 30

    def test_parse_time_string(self):
        assert self.scraper._parse_time('30 minutes') == 30

    def test_parse_time_none(self):
        assert self.scraper._parse_time(None) is None

    def test_parse_time_invalid_string(self):
        assert self.scraper._parse_time('no numbers here') is None

    def test_parse_servings_valid(self):
        assert self.scraper._parse_servings('24 cookies') == 24
        assert self.scraper._parse_servings('6 servings') == 6
        assert self.scraper._parse_servings('Makes 12') == 12

    def test_parse_servings_none(self):
        assert self.scraper._parse_servings(None) is None
        assert self.scraper._parse_servings('') is None

    def test_parse_rating_float(self):
        assert self.scraper._parse_rating(4.5) == 4.5

    def test_parse_rating_string(self):
        assert self.scraper._parse_rating('4.5') == 4.5

    def test_parse_rating_int(self):
        assert self.scraper._parse_rating(4) == 4.0

    def test_parse_rating_none(self):
        assert self.scraper._parse_rating(None) is None

    def test_parse_rating_invalid(self):
        assert self.scraper._parse_rating('not a number') is None

    def test_parse_rating_count_int(self):
        assert self.scraper._parse_rating_count(1500) == 1500

    def test_parse_rating_count_string(self):
        assert self.scraper._parse_rating_count('1500') == 1500

    def test_parse_rating_count_none(self):
        assert self.scraper._parse_rating_count(None) is None

    def test_is_image_url_jpg(self):
        assert self.scraper._is_image_url('https://example.com/photo.jpg') is True

    def test_is_image_url_png(self):
        assert self.scraper._is_image_url('https://example.com/photo.png') is True

    def test_is_image_url_webp(self):
        assert self.scraper._is_image_url('https://example.com/photo.webp') is True

    def test_is_image_url_not_image(self):
        assert self.scraper._is_image_url('https://example.com/page.html') is False

    def test_generate_image_filename_jpg(self):
        filename = self.scraper._generate_image_filename(
            'https://example.com/recipe/123',
            'https://example.com/images/photo.jpg'
        )
        assert filename.startswith('recipe_')
        assert filename.endswith('.jpg')
        assert len(filename) == len('recipe_') + 12 + len('.jpg')

    def test_generate_image_filename_png(self):
        filename = self.scraper._generate_image_filename(
            'https://example.com/recipe/123',
            'https://example.com/images/photo.png'
        )
        assert filename.endswith('.png')

    def test_generate_image_filename_no_extension(self):
        filename = self.scraper._generate_image_filename(
            'https://example.com/recipe/123',
            'https://example.com/images/photo'
        )
        assert filename.endswith('.jpg')  # default


class TestScraperSafeGet:
    """Tests for safe attribute access."""

    def setup_method(self):
        self.scraper = RecipeScraper()

    def test_safe_get_callable(self):
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = 'Test Recipe'
        assert self.scraper._safe_get(mock_scraper, 'title') == 'Test Recipe'

    def test_safe_get_returns_none(self):
        mock_scraper = MagicMock()
        mock_scraper.title.return_value = None
        assert self.scraper._safe_get(mock_scraper, 'title', 'default') == 'default'

    def test_safe_get_exception(self):
        mock_scraper = MagicMock()
        mock_scraper.title.side_effect = Exception('Error')
        assert self.scraper._safe_get(mock_scraper, 'title', 'default') == 'default'

    def test_safe_get_missing_attr(self):
        mock_scraper = MagicMock(spec=[])
        assert self.scraper._safe_get(mock_scraper, 'nonexistent', 'default') == 'default'


class TestScraperParseRecipe:
    """Tests for recipe parsing logic."""

    def setup_method(self):
        self.scraper = RecipeScraper()

    @patch('apps.recipes.services.scraper.scrape_html')
    def test_parse_recipe_basic(self, mock_scrape_html):
        mock_recipe = MagicMock()
        mock_recipe.title.return_value = 'Chocolate Chip Cookies'
        mock_recipe.canonical_url.return_value = 'https://example.com/recipe'
        mock_recipe.site_name.return_value = 'Example Site'
        mock_recipe.author.return_value = 'Chef Test'
        mock_recipe.description.return_value = 'Delicious cookies'
        mock_recipe.image.return_value = 'https://example.com/image.jpg'
        mock_recipe.ingredients.return_value = ['flour', 'sugar']
        mock_recipe.ingredient_groups.return_value = []
        mock_recipe.instructions_list.return_value = ['Mix', 'Bake']
        mock_recipe.instructions.return_value = 'Mix. Bake.'
        mock_recipe.prep_time.return_value = 15
        mock_recipe.cook_time.return_value = 12
        mock_recipe.total_time.return_value = 27
        mock_recipe.yields.return_value = '24 cookies'
        mock_recipe.category.return_value = 'Dessert'
        mock_recipe.cuisine.return_value = 'American'
        mock_recipe.cooking_method.return_value = 'Baking'
        mock_recipe.keywords.return_value = ['cookies']
        mock_recipe.dietary_restrictions.return_value = []
        mock_recipe.equipment.return_value = ['bowl']
        mock_recipe.nutrients.return_value = {'calories': '100'}
        mock_recipe.ratings.return_value = 4.5
        mock_recipe.ratings_count.return_value = 100
        mock_recipe.language.return_value = 'en'
        mock_recipe.links.return_value = []

        mock_scrape_html.return_value = mock_recipe

        result = self.scraper._parse_recipe(
            '<html></html>',
            'https://www.example.com/recipe/123'
        )

        assert result['title'] == 'Chocolate Chip Cookies'
        assert result['host'] == 'example.com'
        assert result['ingredients'] == ['flour', 'sugar']
        assert result['instructions'] == ['Mix', 'Bake']
        assert result['prep_time'] == 15
        assert result['servings'] == 24

    @patch('apps.recipes.services.scraper.scrape_html')
    def test_parse_recipe_no_title_raises(self, mock_scrape_html):
        mock_recipe = MagicMock()
        mock_recipe.title.return_value = None
        mock_recipe.yields.return_value = ''  # Ensure yields returns string, not MagicMock
        mock_scrape_html.return_value = mock_recipe

        with pytest.raises(ParseError, match='no title'):
            self.scraper._parse_recipe('<html></html>', 'https://example.com')

    @patch('apps.recipes.services.scraper.scrape_html')
    def test_parse_recipe_scraper_exception(self, mock_scrape_html):
        mock_scrape_html.side_effect = Exception('Parse failed')

        with pytest.raises(ParseError, match='Parse failed'):
            self.scraper._parse_recipe('<html></html>', 'https://example.com')


@pytest.mark.django_db(transaction=True)
class TestScraperIntegration:
    """Integration tests for recipe scraper."""

    @pytest.fixture
    def test_profile(self, db):
        """Create a test profile for recipe ownership."""
        from apps.profiles.models import Profile
        return Profile.objects.create(name='Test User', avatar_color='#d97850')

    @pytest.fixture
    def mock_html_response(self):
        """Mock HTML with JSON-LD recipe data."""
        return '''
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Recipe",
                "name": "Simple Test Cookies",
                "author": {"@type": "Person", "name": "Test Chef"},
                "description": "Easy to make cookies",
                "image": "https://example.com/cookie.jpg",
                "recipeIngredient": ["1 cup flour", "1/2 cup sugar"],
                "recipeInstructions": [
                    {"@type": "HowToStep", "text": "Mix ingredients"},
                    {"@type": "HowToStep", "text": "Bake at 350F"}
                ],
                "prepTime": "PT15M",
                "cookTime": "PT12M",
                "totalTime": "PT27M",
                "recipeYield": "12 cookies"
            }
            </script>
        </head>
        <body><h1>Simple Test Cookies</h1></body>
        </html>
        '''

    @patch('apps.recipes.services.scraper.AsyncSession')
    async def test_scrape_url_creates_recipe(self, mock_session_class, mock_html_response, test_profile):
        """Test that scraping a URL creates a Recipe record."""
        from apps.recipes.models import Recipe

        # Mock the session and response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html_response
        mock_response.headers = {'content-type': 'text/html'}

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        # Mock image response (empty/failed)
        mock_img_response = MagicMock()
        mock_img_response.status_code = 404
        mock_session.get.side_effect = [mock_response, mock_img_response]

        scraper = RecipeScraper()
        recipe = await scraper.scrape_url('https://www.example.com/recipe/test', test_profile)

        assert recipe.id is not None
        assert recipe.title == 'Simple Test Cookies'
        assert recipe.host == 'example.com'
        assert recipe.profile_id == test_profile.id
        assert len(recipe.ingredients) == 2
        assert recipe.prep_time == 15
        assert recipe.cook_time == 12
        assert recipe.total_time == 27

    @patch('apps.recipes.services.scraper.AsyncSession')
    async def test_scrape_url_fetch_failure(self, mock_session_class, test_profile):
        """Test that fetch failure raises FetchError."""
        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=Exception('Connection failed'))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        scraper = RecipeScraper()

        with pytest.raises(FetchError, match='Failed to fetch'):
            await scraper.scrape_url('https://example.com/recipe', test_profile)

    @patch('apps.recipes.services.scraper.AsyncSession')
    async def test_scrape_url_with_image_download(self, mock_session_class, mock_html_response, test_profile):
        """Test that recipe images are downloaded and saved."""
        from apps.recipes.models import Recipe

        # Mock HTML response
        mock_html_resp = MagicMock()
        mock_html_resp.status_code = 200
        mock_html_resp.text = mock_html_response

        # Mock image response
        mock_img_resp = MagicMock()
        mock_img_resp.status_code = 200
        mock_img_resp.content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'  # PNG header
        mock_img_resp.headers = {'content-type': 'image/png'}

        mock_session = MagicMock()
        mock_session.get = AsyncMock(side_effect=[mock_html_resp, mock_img_resp])
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        scraper = RecipeScraper()
        recipe = await scraper.scrape_url('https://www.example.com/recipe/test', test_profile)

        assert recipe.image_url == 'https://example.com/cookie.jpg'
        # Image should be attached
        assert recipe.image.name != ''
