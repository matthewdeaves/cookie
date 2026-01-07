"""Tests for Legacy frontend views and template rendering."""

import pytest
from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeFavorite,
    RecipeViewHistory,
)


@pytest.mark.django_db
class TestLegacyProfileSelector:
    """Tests for the legacy profile selector view."""

    def test_profile_selector_renders(self, client):
        """Profile selector page renders successfully."""
        response = client.get('/legacy/')
        assert response.status_code == 200
        content = response.content.decode()
        assert "Who's cooking today?" in content
        assert 'data-page="profileSelector"' in content

    def test_profile_selector_shows_profiles(self, client):
        """Profile selector displays existing profiles."""
        Profile.objects.create(name='Alice', avatar_color='#d97850')
        Profile.objects.create(name='Bob', avatar_color='#6b8e5f')

        response = client.get('/legacy/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Alice' in content
        assert 'Bob' in content

    def test_profile_selector_empty_state(self, client):
        """Profile selector shows create prompt when no profiles exist."""
        response = client.get('/legacy/')
        assert response.status_code == 200
        content = response.content.decode()
        # Should still show the page even without profiles
        assert "Who's cooking today?" in content


@pytest.mark.django_db
class TestLegacyHome:
    """Tests for the legacy home view."""

    def test_home_redirects_without_profile(self, client):
        """Home redirects to profile selector when no profile in session."""
        response = client.get('/legacy/home/')
        assert response.status_code == 302
        assert response.url == '/legacy/'

    def test_home_renders_with_profile(self, client):
        """Home renders when profile is selected."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/home/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="home"' in content
        assert 'Search recipes' in content

    def test_home_shows_favorites_tab(self, client):
        """Home shows favorites/discover tabs."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/home/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'My Favorites' in content
        assert 'Discover' in content

    def test_home_shows_favorite_recipes(self, client):
        """Home displays user's favorite recipes."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Test Recipe' in content

    def test_home_shows_recently_viewed(self, client):
        """Home displays recently viewed recipes."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Viewed Recipe',
            host='example.com',
            site_name='Example',
        )
        RecipeViewHistory.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Recently Viewed' in content
        assert 'Viewed Recipe' in content

    def test_home_empty_state(self, client):
        """Home shows empty state when no favorites."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/home/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'No favorites yet' in content

    def test_home_redirects_on_invalid_profile(self, client):
        """Home redirects if profile in session doesn't exist."""
        # Set invalid profile_id in session
        session = client.session
        session['profile_id'] = 99999
        session.save()

        response = client.get('/legacy/home/')
        assert response.status_code == 302
        assert response.url == '/legacy/'


@pytest.mark.django_db
class TestLegacySearch:
    """Tests for the legacy search view."""

    def test_search_redirects_without_profile(self, client):
        """Search redirects to profile selector when no profile in session."""
        response = client.get('/legacy/search/?q=cookies')
        assert response.status_code == 302
        assert response.url == '/legacy/'

    def test_search_renders_with_query(self, client):
        """Search renders with the query parameter."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=cookies')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="search"' in content
        assert 'cookies' in content

    def test_search_displays_query_text(self, client):
        """Search displays the search query to the user."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=chocolate%20cake')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'chocolate cake' in content

    def test_search_url_import_mode(self, client):
        """Search shows URL import card when query is a URL."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=https://example.com/recipe')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'Import Recipe from URL' in content
        assert 'url-import-card' in content

    def test_search_not_url_mode(self, client):
        """Search shows regular search mode for non-URL queries."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=pasta')
        assert response.status_code == 200
        content = response.content.decode()
        # Should have source filters div (for JS to populate)
        assert 'source-filters' in content
        # Should NOT have URL import card
        assert 'url-import-card' not in content

    def test_search_back_button_present(self, client):
        """Search page has back button to home."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=test')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'back-btn' in content

    def test_search_empty_query(self, client):
        """Search handles empty query gracefully."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="search"' in content


@pytest.mark.django_db
class TestLegacyTemplateRendering:
    """Tests for legacy template rendering and structure."""

    def test_base_template_includes_css(self, client):
        """Base template includes all required CSS files."""
        response = client.get('/legacy/')
        content = response.content.decode()
        assert 'legacy/css/base.css' in content
        assert 'legacy/css/components.css' in content
        assert 'legacy/css/layout.css' in content

    def test_base_template_includes_js(self, client):
        """Base template includes all required JS files."""
        response = client.get('/legacy/')
        content = response.content.decode()
        assert 'legacy/js/polyfills.js' in content
        assert 'legacy/js/ajax.js' in content
        assert 'legacy/js/state.js' in content
        assert 'legacy/js/toast.js' in content
        assert 'legacy/js/app.js' in content

    def test_base_template_has_toast_container(self, client):
        """Base template includes toast notification container."""
        response = client.get('/legacy/')
        content = response.content.decode()
        assert 'toast-container' in content

    def test_home_includes_page_js(self, client):
        """Home page includes its specific JS file."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert 'legacy/js/pages/home.js' in content

    def test_search_includes_page_js(self, client):
        """Search page includes its specific JS file."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/search/?q=test')
        content = response.content.decode()
        assert 'legacy/js/pages/search.js' in content

    def test_profile_selector_includes_page_js(self, client):
        """Profile selector includes its specific JS file."""
        response = client.get('/legacy/')
        content = response.content.decode()
        assert 'legacy/js/pages/profile-selector.js' in content


@pytest.mark.django_db
class TestLegacyRecipeCard:
    """Tests for the recipe card partial rendering."""

    def test_recipe_card_shows_title(self, client):
        """Recipe card displays the recipe title."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Chocolate Chip Cookies',
            host='example.com',
            site_name='Example',
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert 'Chocolate Chip Cookies' in content

    def test_recipe_card_shows_source(self, client):
        """Recipe card displays the source host."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='allrecipes.com',
            site_name='Allrecipes',
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert 'allrecipes.com' in content

    def test_recipe_card_shows_time(self, client):
        """Recipe card displays total time when available."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            total_time=45,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert '45' in content  # Time display

    def test_recipe_card_shows_rating(self, client):
        """Recipe card displays rating when available."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            rating=4.5,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert '4.5' in content

    def test_recipe_card_shows_remix_badge(self, client):
        """Recipe card displays remix badge for remixed recipes."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Remixed Recipe',
            host='user-generated',
            site_name='User Generated',
            is_remix=True,
            remix_profile=profile,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f'/api/profiles/{profile.id}/select/')
        response = client.get('/legacy/home/')
        content = response.content.decode()
        assert 'Remix' in content
        assert 'recipe-card-badge' in content


@pytest.mark.django_db
class TestLegacyRecipeDetail:
    """Tests for the legacy recipe detail view."""

    def test_recipe_detail_redirects_without_profile(self, client):
        """Recipe detail redirects to profile selector when no profile in session."""
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        response = client.get(f'/legacy/recipe/{recipe.id}/')
        assert response.status_code == 302
        assert response.url == '/legacy/'

    def test_recipe_detail_renders(self, client):
        """Recipe detail renders successfully with profile."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Chocolate Chip Cookies',
            host='example.com',
            site_name='Example',
            description='Delicious cookies',
            ingredients=['2 cups flour', '1 cup sugar', '1 cup butter'],
            instructions=['Mix ingredients', 'Bake at 350F for 10 minutes'],
            rating=4.5,
            rating_count=100,
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="recipe-detail"' in content
        assert 'Chocolate Chip Cookies' in content

    def test_recipe_detail_shows_all_tabs(self, client):
        """Recipe detail shows all four tabs."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert 'tab-ingredients' in content
        assert 'tab-instructions' in content
        assert 'tab-nutrition' in content
        assert 'tab-tips' in content

    def test_recipe_detail_shows_ingredients(self, client):
        """Recipe detail displays ingredients list."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            ingredients=['2 cups flour', '1 cup sugar'],
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert '2 cups flour' in content
        assert '1 cup sugar' in content

    def test_recipe_detail_shows_instructions(self, client):
        """Recipe detail displays instructions."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            instructions=['Step 1: Mix', 'Step 2: Bake'],
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert 'Step 1: Mix' in content
        assert 'Step 2: Bake' in content

    def test_recipe_detail_shows_nutrition(self, client):
        """Recipe detail displays nutrition info when available."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            nutrition={'calories': '200', 'protein': '5g'},
            servings=4,
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert 'calories' in content
        assert '200' in content

    def test_recipe_detail_records_view_history(self, client):
        """Recipe detail creates/updates view history."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        assert RecipeViewHistory.objects.count() == 0
        client.get(f'/legacy/recipe/{recipe.id}/')
        assert RecipeViewHistory.objects.count() == 1
        history = RecipeViewHistory.objects.first()
        assert history.profile == profile
        assert history.recipe == recipe

    def test_recipe_detail_shows_favorite_state(self, client):
        """Recipe detail shows correct favorite button state."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        # Check that favorite button has active class
        assert 'hero-action-btn active' in content

    def test_recipe_detail_shows_collections(self, client):
        """Recipe detail shows user's collections in modal."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        RecipeCollection.objects.create(profile=profile, name='Weeknight Dinners')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert 'Weeknight Dinners' in content

    def test_recipe_detail_404_for_nonexistent(self, client):
        """Recipe detail returns 404 for non-existent recipe."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get('/legacy/recipe/99999/')
        assert response.status_code == 404

    def test_recipe_detail_hides_other_remix(self, client):
        """Recipe detail redirects when trying to view another user's remix."""
        profile1 = Profile.objects.create(name='User1', avatar_color='#d97850')
        profile2 = Profile.objects.create(name='User2', avatar_color='#6b8e5f')
        remix = Recipe.objects.create(
            title='Private Remix',
            host='user-generated',
            site_name='User Generated',
            is_remix=True,
            remix_profile=profile2,
        )
        client.post(f'/api/profiles/{profile1.id}/select/')

        response = client.get(f'/legacy/recipe/{remix.id}/')
        assert response.status_code == 302  # Redirects to home

    def test_recipe_detail_shows_own_remix(self, client):
        """Recipe detail shows user's own remix."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        remix = Recipe.objects.create(
            title='My Remix',
            host='user-generated',
            site_name='User Generated',
            is_remix=True,
            remix_profile=profile,
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{remix.id}/')
        assert response.status_code == 200
        content = response.content.decode()
        assert 'My Remix' in content

    def test_recipe_detail_includes_css_and_js(self, client):
        """Recipe detail includes page-specific CSS and JS."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        assert 'legacy/css/recipe-detail.css' in content
        assert 'legacy/js/pages/detail.js' in content

    def test_recipe_detail_shows_serving_adjuster_without_ai(self, client):
        """Recipe detail shows static servings when AI not configured."""
        profile = Profile.objects.create(name='Test', avatar_color='#d97850')
        recipe = Recipe.objects.create(
            title='Test Recipe',
            host='example.com',
            site_name='Example',
            servings=4,
        )
        client.post(f'/api/profiles/{profile.id}/select/')

        response = client.get(f'/legacy/recipe/{recipe.id}/')
        content = response.content.decode()
        # Should show static servings, not adjuster
        assert 'Servings:' in content
        assert 'serving-adjuster' not in content  # Adjuster partial not rendered
