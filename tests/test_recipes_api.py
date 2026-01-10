"""
Tests for recipe API endpoints.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from django.test import Client


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def sample_recipe(db, test_profile):
    """Create a sample recipe for testing."""
    from apps.recipes.models import Recipe
    return Recipe.objects.create(
        profile=test_profile,
        host='allrecipes.com',
        title='Test Chocolate Chip Cookies',
        source_url='https://www.allrecipes.com/recipe/12345/test-cookies/',
        description='Delicious test cookies',
        ingredients=['1 cup flour', '1/2 cup sugar'],
        instructions=['Mix', 'Bake'],
        prep_time=15,
        cook_time=12,
        total_time=27,
        rating=4.5,
    )


@pytest.fixture
def test_profile(db):
    """Create a profile for testing remix visibility."""
    from apps.profiles.models import Profile
    return Profile.objects.create(name='Test User', avatar_color='#123456')


@pytest.fixture
def multiple_recipes(db, test_profile):
    """Create multiple recipes for list/filter testing."""
    from apps.recipes.models import Recipe
    recipes = []
    recipes.append(Recipe.objects.create(
        profile=test_profile,
        host='allrecipes.com',
        title='Cookies Recipe',
        is_remix=False,
    ))
    recipes.append(Recipe.objects.create(
        profile=test_profile,
        host='allrecipes.com',
        title='Brownies Recipe',
        is_remix=False,
    ))
    recipes.append(Recipe.objects.create(
        profile=test_profile,
        host='bbcgoodfood.com',
        title='Scones Recipe',
        is_remix=False,
    ))
    recipes.append(Recipe.objects.create(
        profile=test_profile,
        host='cookie.local',
        title='My Remix Recipe',
        is_remix=True,
        remix_profile=test_profile,  # Assign remix to test profile
    ))
    return recipes


@pytest.mark.django_db
class TestListRecipes:
    """Tests for GET /api/recipes/"""

    def test_list_recipes_empty(self, client):
        """Test listing recipes when none exist."""
        response = client.get('/api/recipes/')
        assert response.status_code == 200
        assert response.json() == []

    def test_list_recipes_returns_recipes(self, client, sample_recipe, test_profile):
        """Test listing recipes returns existing recipes."""
        # Select the profile that owns the recipes
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get('/api/recipes/')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['title'] == 'Test Chocolate Chip Cookies'
        assert data[0]['host'] == 'allrecipes.com'

    def test_list_recipes_filter_by_host(self, client, multiple_recipes, test_profile):
        """Test filtering recipes by host."""
        # Select the profile that owns the recipes
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get('/api/recipes/?host=allrecipes.com')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(r['host'] == 'allrecipes.com' for r in data)

    def test_list_recipes_filter_by_remix(self, client, multiple_recipes, test_profile):
        """Test filtering recipes by is_remix (requires profile for visibility)."""
        # Select the profile that owns the remix
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get('/api/recipes/?is_remix=true')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]['is_remix'] is True
        assert data[0]['title'] == 'My Remix Recipe'

    def test_list_recipes_filter_non_remixes(self, client, multiple_recipes, test_profile):
        """Test filtering non-remix recipes."""
        # Select the profile that owns the recipes
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get('/api/recipes/?is_remix=false')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(r['is_remix'] is False for r in data)

    def test_list_recipes_pagination(self, client, multiple_recipes, test_profile):
        """Test pagination with limit and offset."""
        # Select the profile that owns the recipes
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get('/api/recipes/?limit=2&offset=0')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

        response = client.get('/api/recipes/?limit=2&offset=2')
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # 4 total recipes (3 non-remix + 1 remix)


@pytest.mark.django_db
class TestGetRecipe:
    """Tests for GET /api/recipes/{id}/"""

    def test_get_recipe_success(self, client, sample_recipe, test_profile):
        """Test getting a recipe by ID."""
        # Select the profile that owns the recipe
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get(f'/api/recipes/{sample_recipe.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['id'] == sample_recipe.id
        assert data['title'] == 'Test Chocolate Chip Cookies'
        assert data['host'] == 'allrecipes.com'
        assert data['ingredients'] == ['1 cup flour', '1/2 cup sugar']
        assert data['instructions'] == ['Mix', 'Bake']
        assert data['prep_time'] == 15
        assert data['cook_time'] == 12
        assert data['total_time'] == 27
        assert data['rating'] == 4.5

    def test_get_recipe_not_found(self, client, test_profile):
        """Test getting a non-existent recipe returns 404."""
        client.post(f'/api/profiles/{test_profile.id}/select/')
        response = client.get('/api/recipes/99999/')
        assert response.status_code == 404

    def test_get_recipe_full_fields(self, client, db, test_profile):
        """Test that all recipe fields are returned."""
        from apps.recipes.models import Recipe
        recipe = Recipe.objects.create(
            profile=test_profile,
            host='test.com',
            title='Full Recipe',
            source_url='https://test.com/recipe',
            canonical_url='https://test.com/recipe',
            site_name='Test Site',
            author='Test Author',
            description='Test description',
            image_url='https://test.com/image.jpg',
            ingredients=['ingredient 1'],
            ingredient_groups=[{'purpose': 'Base', 'ingredients': ['flour']}],
            instructions=['step 1'],
            instructions_text='Step 1',
            prep_time=10,
            cook_time=20,
            total_time=30,
            yields='6 servings',
            servings=6,
            category='Dessert',
            cuisine='American',
            cooking_method='Baking',
            keywords=['test', 'recipe'],
            dietary_restrictions=['vegetarian'],
            equipment=['bowl'],
            nutrition={'calories': '100'},
            rating=4.0,
            rating_count=50,
            language='en',
            links=['https://related.com'],
            ai_tips=['tip 1'],
            is_remix=False,
        )

        # Select the profile that owns the recipe
        client.post(f'/api/profiles/{test_profile.id}/select/')

        response = client.get(f'/api/recipes/{recipe.id}/')
        assert response.status_code == 200
        data = response.json()

        # Verify all fields are present
        assert data['source_url'] == 'https://test.com/recipe'
        assert data['canonical_url'] == 'https://test.com/recipe'
        assert data['site_name'] == 'Test Site'
        assert data['author'] == 'Test Author'
        assert data['category'] == 'Dessert'
        assert data['cuisine'] == 'American'
        assert data['keywords'] == ['test', 'recipe']
        assert data['nutrition'] == {'calories': '100'}
        assert data['ai_tips'] == ['tip 1']


@pytest.mark.django_db
class TestDeleteRecipe:
    """Tests for DELETE /api/recipes/{id}/"""

    def test_delete_recipe_success(self, client, sample_recipe, test_profile):
        """Test deleting a recipe."""
        from apps.recipes.models import Recipe

        # Select the profile that owns the recipe
        client.post(f'/api/profiles/{test_profile.id}/select/')

        recipe_id = sample_recipe.id
        response = client.delete(f'/api/recipes/{recipe_id}/')
        assert response.status_code == 204

        # Verify it's deleted
        assert not Recipe.objects.filter(id=recipe_id).exists()

    def test_delete_recipe_not_found(self, client, test_profile):
        """Test deleting a non-existent recipe returns 404."""
        client.post(f'/api/profiles/{test_profile.id}/select/')
        response = client.delete('/api/recipes/99999/')
        assert response.status_code == 404


@pytest.mark.django_db(transaction=True)
class TestScrapeRecipe:
    """Tests for POST /api/recipes/scrape/"""

    @patch('apps.recipes.api.aget_current_profile_or_none')
    @patch('apps.recipes.api.RecipeScraper')
    async def test_scrape_recipe_success(self, mock_scraper_class, mock_get_profile, db):
        """Test scraping a recipe successfully."""
        from asgiref.sync import sync_to_async
        from apps.profiles.models import Profile
        from datetime import datetime
        from unittest.mock import AsyncMock

        # Create profile synchronously using sync_to_async
        @sync_to_async
        def create_profile():
            return Profile.objects.create(name='Test User', avatar_color='#123456')

        test_profile = await create_profile()

        # Mock the async profile lookup to return our test profile
        mock_get_profile.return_value = test_profile

        # Create a simple object with all fields RecipeOut needs
        # (avoids MagicMock's dynamic attribute creation issue)
        class MockRecipe:
            id = 1
            source_url = 'https://example.com/recipe/123'
            canonical_url = 'https://example.com/recipe/123'
            host = 'example.com'
            site_name = ''
            title = 'Test Recipe'
            author = ''
            description = ''
            image_url = ''
            image = None
            ingredients = []
            ingredient_groups = []
            instructions = []
            instructions_text = ''
            prep_time = None
            cook_time = None
            total_time = None
            yields = ''
            servings = None
            category = ''
            cuisine = ''
            cooking_method = ''
            keywords = []
            dietary_restrictions = []
            equipment = []
            nutrition = {}
            rating = None
            rating_count = None
            language = ''
            links = []
            ai_tips = []
            is_remix = False
            remix_profile_id = None
            scraped_at = datetime.now()
            updated_at = datetime.now()

        mock_recipe = MockRecipe()

        mock_scraper = MagicMock()
        mock_scraper.scrape_url = AsyncMock(return_value=mock_recipe)
        mock_scraper_class.return_value = mock_scraper

        from django.test import AsyncClient
        async_client = AsyncClient()

        response = await async_client.post(
            '/api/recipes/scrape/',
            {'url': 'https://example.com/recipe/123'},
            content_type='application/json',
        )

        assert response.status_code == 201
        data = response.json()
        assert data['title'] == 'Test Recipe'
        assert data['host'] == 'example.com'

    @patch('apps.recipes.api.aget_current_profile_or_none')
    @patch('apps.recipes.api.RecipeScraper')
    async def test_scrape_recipe_fetch_error(self, mock_scraper_class, mock_get_profile, db):
        """Test scraping returns 502 on fetch error."""
        from asgiref.sync import sync_to_async
        from apps.recipes.services.scraper import FetchError
        from apps.profiles.models import Profile

        @sync_to_async
        def create_profile():
            return Profile.objects.create(name='Test User', avatar_color='#123456')

        test_profile = await create_profile()

        # Mock the async profile lookup
        mock_get_profile.return_value = test_profile

        mock_scraper = MagicMock()
        mock_scraper.scrape_url = AsyncMock(side_effect=FetchError('Connection failed'))
        mock_scraper_class.return_value = mock_scraper

        from django.test import AsyncClient
        async_client = AsyncClient()

        response = await async_client.post(
            '/api/recipes/scrape/',
            {'url': 'https://example.com/recipe/123'},
            content_type='application/json',
        )

        assert response.status_code == 502
        data = response.json()
        assert 'Connection failed' in data['detail']

    @patch('apps.recipes.api.aget_current_profile_or_none')
    @patch('apps.recipes.api.RecipeScraper')
    async def test_scrape_recipe_parse_error(self, mock_scraper_class, mock_get_profile, db):
        """Test scraping returns 400 on parse error."""
        from asgiref.sync import sync_to_async
        from apps.recipes.services.scraper import ParseError
        from apps.profiles.models import Profile

        @sync_to_async
        def create_profile():
            return Profile.objects.create(name='Test User', avatar_color='#123456')

        test_profile = await create_profile()

        # Mock the async profile lookup
        mock_get_profile.return_value = test_profile

        mock_scraper = MagicMock()
        mock_scraper.scrape_url = AsyncMock(side_effect=ParseError('Recipe has no title'))
        mock_scraper_class.return_value = mock_scraper

        from django.test import AsyncClient
        async_client = AsyncClient()

        response = await async_client.post(
            '/api/recipes/scrape/',
            {'url': 'https://example.com/recipe/123'},
            content_type='application/json',
        )

        assert response.status_code == 400
        data = response.json()
        assert 'no title' in data['detail']

    async def test_scrape_recipe_requires_profile(self, db):
        """Test scraping requires a profile."""
        from django.test import AsyncClient
        async_client = AsyncClient()
        response = await async_client.post(
            '/api/recipes/scrape/',
            {'url': 'https://example.com/recipe/123'},
            content_type='application/json',
        )

        assert response.status_code == 403
        data = response.json()
        assert 'Profile required' in data['detail']


@pytest.mark.django_db
class TestSearchRecipesAPI:
    """Tests for GET /api/recipes/search/"""

    @patch('apps.recipes.api.RecipeSearch')
    async def test_search_recipes_basic(self, mock_search_class):
        """Test basic recipe search."""
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={
            'results': [
                {
                    'url': 'https://example.com/recipe/123',
                    'title': 'Chocolate Cookies',
                    'host': 'example.com',
                    'image_url': 'https://example.com/image.jpg',
                    'description': 'Yummy cookies',
                }
            ],
            'total': 1,
            'page': 1,
            'has_more': False,
            'sites': {'example.com': 1},
        })
        mock_search_class.return_value = mock_search

        from django.test import AsyncClient
        async_client = AsyncClient()
        response = await async_client.get('/api/recipes/search/?q=chocolate+cookies')

        assert response.status_code == 200
        data = response.json()
        assert data['total'] == 1
        assert len(data['results']) == 1
        assert data['results'][0]['title'] == 'Chocolate Cookies'

    @patch('apps.recipes.api.RecipeSearch')
    async def test_search_recipes_with_source_filter(self, mock_search_class):
        """Test recipe search with source filter."""
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={
            'results': [],
            'total': 0,
            'page': 1,
            'has_more': False,
            'sites': {},
        })
        mock_search_class.return_value = mock_search

        from django.test import AsyncClient
        async_client = AsyncClient()
        response = await async_client.get(
            '/api/recipes/search/?q=cookies&sources=allrecipes.com,bbcgoodfood.com'
        )

        assert response.status_code == 200

        # Verify search was called with correct sources
        call_args = mock_search.search.call_args
        assert call_args.kwargs['sources'] == ['allrecipes.com', 'bbcgoodfood.com']

    @patch('apps.recipes.api.RecipeSearch')
    async def test_search_recipes_pagination(self, mock_search_class):
        """Test recipe search pagination."""
        mock_search = MagicMock()
        mock_search.search = AsyncMock(return_value={
            'results': [],
            'total': 50,
            'page': 2,
            'has_more': True,
            'sites': {},
        })
        mock_search_class.return_value = mock_search

        from django.test import AsyncClient
        async_client = AsyncClient()
        response = await async_client.get('/api/recipes/search/?q=cookies&page=2&per_page=10')

        assert response.status_code == 200

        # Verify search was called with correct pagination
        call_args = mock_search.search.call_args
        assert call_args.kwargs['page'] == 2
        assert call_args.kwargs['per_page'] == 10

    @patch('apps.recipes.api.RecipeSearch')
    async def test_search_missing_query(self, mock_search_class):
        """Test search without query parameter returns error."""
        from django.test import AsyncClient
        async_client = AsyncClient()
        response = await async_client.get('/api/recipes/search/')

        # Should return 422 (validation error) for missing required parameter
        assert response.status_code == 422


@pytest.mark.django_db(transaction=True)
class TestRecipeScrapeCreatesNewRecords:
    """Test that re-scraping same URL creates new records."""

    @patch('apps.recipes.services.scraper.threading')
    @patch('apps.recipes.services.scraper.AsyncSession')
    async def test_scrape_same_url_twice_creates_two_records(self, mock_session_class, mock_threading, test_profile):
        """Test that scraping same URL twice creates two recipes."""
        from apps.recipes.models import Recipe
        from apps.recipes.services.scraper import RecipeScraper
        from asgiref.sync import sync_to_async

        mock_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Recipe",
                "name": "Test Recipe",
                "recipeIngredient": ["flour"],
                "recipeInstructions": [{"@type": "HowToStep", "text": "Mix"}]
            }
            </script>
        </head>
        <body></body>
        </html>
        '''

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = mock_html
        mock_response.headers = {}

        mock_session = MagicMock()
        mock_session.get = AsyncMock(return_value=mock_response)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        mock_session_class.return_value = mock_session

        url = 'https://example.com/recipe/test'
        scraper = RecipeScraper()

        # Scrape twice (with profile required)
        recipe1 = await scraper.scrape_url(url, test_profile)
        recipe2 = await scraper.scrape_url(url, test_profile)

        # Should be two different records
        assert recipe1.id != recipe2.id

        @sync_to_async
        def count_recipes():
            return Recipe.objects.filter(source_url=url).count()

        assert await count_recipes() == 2
