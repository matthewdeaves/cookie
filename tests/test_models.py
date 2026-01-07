import pytest
from apps.recipes.models import Recipe, SearchSource
from apps.profiles.models import Profile


@pytest.mark.django_db
class TestRecipeModel:
    def test_create_recipe_minimal(self):
        """Test creating a recipe with minimal required fields."""
        recipe = Recipe.objects.create(
            host='allrecipes.com',
            title='Chocolate Chip Cookies',
        )
        assert recipe.id is not None
        assert recipe.title == 'Chocolate Chip Cookies'
        assert recipe.host == 'allrecipes.com'
        assert str(recipe) == 'Chocolate Chip Cookies'

    def test_create_recipe_full(self):
        """Test creating a recipe with all fields populated."""
        recipe = Recipe.objects.create(
            source_url='https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/',
            canonical_url='https://www.allrecipes.com/recipe/10813/best-chocolate-chip-cookies/',
            host='allrecipes.com',
            site_name='AllRecipes',
            title='Best Chocolate Chip Cookies',
            author='Dora Thomas',
            description='Crispy on the outside, chewy on the inside.',
            image_url='https://example.com/cookie.jpg',
            ingredients=['2 cups flour', '1 cup sugar', '1 cup chocolate chips'],
            ingredient_groups=[{'name': 'Dry', 'items': ['2 cups flour']}],
            instructions=['Mix dry ingredients', 'Add wet ingredients', 'Bake'],
            instructions_text='Mix dry ingredients. Add wet ingredients. Bake.',
            prep_time=15,
            cook_time=12,
            total_time=27,
            yields='24 cookies',
            servings=24,
            category='Dessert',
            cuisine='American',
            cooking_method='Baking',
            keywords=['cookies', 'chocolate', 'dessert'],
            dietary_restrictions=[],
            equipment=['Mixing bowl', 'Baking sheet'],
            nutrition={'calories': '150', 'fat': '8g'},
            rating=4.8,
            rating_count=1523,
            language='en',
            links=['https://example.com/related'],
            ai_tips=['Use room temperature butter'],
            is_remix=False,
        )

        assert recipe.id is not None
        assert recipe.prep_time == 15
        assert recipe.cook_time == 12
        assert recipe.total_time == 27
        assert recipe.servings == 24
        assert recipe.rating == 4.8
        assert len(recipe.ingredients) == 3
        assert len(recipe.instructions) == 3
        assert recipe.nutrition['calories'] == '150'

    def test_recipe_default_json_fields(self):
        """Test that JSON fields have correct default values."""
        recipe = Recipe.objects.create(
            host='test.com',
            title='Test Recipe',
        )
        assert recipe.ingredients == []
        assert recipe.ingredient_groups == []
        assert recipe.instructions == []
        assert recipe.keywords == []
        assert recipe.dietary_restrictions == []
        assert recipe.equipment == []
        assert recipe.nutrition == {}
        assert recipe.links == []
        assert recipe.ai_tips == []

    def test_recipe_remix_relationship(self):
        """Test recipe remix relationship with Profile."""
        profile = Profile.objects.create(
            name='Test Chef',
            avatar_color='#FF5733',
        )
        original = Recipe.objects.create(
            host='allrecipes.com',
            title='Original Recipe',
        )
        remix = Recipe.objects.create(
            host='cookie.local',
            title='My Remix',
            is_remix=True,
            remix_profile=profile,
        )

        assert remix.is_remix is True
        assert remix.remix_profile == profile
        assert profile.remixes.count() == 1
        assert profile.remixes.first() == remix

    def test_recipe_indexes_exist(self):
        """Test that model indexes are defined."""
        index_fields = [idx.fields for idx in Recipe._meta.indexes]
        assert ['host'] in index_fields
        assert ['is_remix'] in index_fields
        assert ['scraped_at'] in index_fields


@pytest.mark.django_db
class TestSearchSourceModel:
    def test_search_source_count(self):
        """Test that 15 search sources were created by migration."""
        assert SearchSource.objects.count() == 15

    def test_search_source_fields(self):
        """Test that search sources have required fields."""
        allrecipes = SearchSource.objects.get(host='allrecipes.com')
        assert allrecipes.name == 'AllRecipes'
        assert allrecipes.is_enabled is True
        assert '{query}' in allrecipes.search_url_template
        assert allrecipes.consecutive_failures == 0
        assert allrecipes.needs_attention is False

    def test_search_source_str(self):
        """Test SearchSource string representation."""
        source = SearchSource.objects.get(host='bbcgoodfood.com')
        assert str(source) == 'BBC Good Food'

    def test_search_source_ordering(self):
        """Test that sources are ordered by name."""
        sources = list(SearchSource.objects.all())
        names = [s.name for s in sources]
        assert names == sorted(names)

    def test_all_sources_present(self):
        """Test that all 15 expected sources exist."""
        expected_hosts = [
            'allrecipes.com',
            'bbcgoodfood.com',
            'bbc.co.uk',
            'bonappetit.com',
            'budgetbytes.com',
            'delish.com',
            'epicurious.com',
            'foodnetwork.com',
            'food52.com',
            'jamieoliver.com',
            'tasty.co',
            'seriouseats.com',
            'simplyrecipes.com',
            'tasteofhome.com',
            'thekitchn.com',
        ]
        for host in expected_hosts:
            assert SearchSource.objects.filter(host=host).exists(), f'{host} not found'

    def test_search_source_unique_host(self):
        """Test that host field is unique."""
        with pytest.raises(Exception):  # IntegrityError
            SearchSource.objects.create(
                host='allrecipes.com',  # Already exists
                name='Duplicate',
                search_url_template='https://example.com',
            )
