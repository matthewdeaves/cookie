"""Tests for Legacy frontend views: profile selector, home, search, nav header, and template rendering."""

import pytest

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeFavorite,
    RecipeViewHistory,
)


@pytest.mark.django_db
class TestLegacyProfileSelector:
    """Tests for the legacy profile selector view."""

    def test_profile_selector_renders(self, client):
        """Profile selector page renders successfully."""
        response = client.get("/legacy/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Who's cooking today?" in content
        assert 'data-page="profileSelector"' in content

    def test_profile_selector_shows_profiles(self, client):
        """Profile selector displays existing profiles."""
        Profile.objects.create(name="Alice", avatar_color="#d97850")
        Profile.objects.create(name="Bob", avatar_color="#6b8e5f")

        response = client.get("/legacy/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Alice" in content
        assert "Bob" in content

    def test_profile_selector_empty_state(self, client):
        """Profile selector shows create prompt when no profiles exist."""
        response = client.get("/legacy/")
        assert response.status_code == 200
        content = response.content.decode()
        # Should still show the page even without profiles
        assert "Who's cooking today?" in content


@pytest.mark.django_db
class TestLegacyHome:
    """Tests for the legacy home view."""

    def test_home_redirects_without_profile(self, client):
        """Home redirects to profile selector when no profile in session."""
        response = client.get("/legacy/home/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_home_renders_with_profile(self, client):
        """Home renders when profile is selected."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/home/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="home"' in content
        assert "Search recipes" in content

    def test_home_shows_empty_favorites_section(self, client):
        """Home shows favorites section with empty state when no favorites exist."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/home/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "My Favorite Recipes" in content
        assert "No favorites yet" in content

    def test_home_shows_favorite_recipes(self, client):
        """Home displays user's favorite recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Recipe" in content

    def test_home_shows_recently_viewed(self, client):
        """Home displays recently viewed recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Viewed Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeViewHistory.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Recently Viewed" in content
        assert "Viewed Recipe" in content

    def test_home_shows_my_recipes_link_with_count(self, client):
        """Home shows 'My Recipes' link with total recipe count."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        # Create 3 recipes (mix of imports and remixes)
        Recipe.objects.create(
            profile=profile,
            title="Recipe 1",
            host="example.com",
            site_name="Example",
        )
        Recipe.objects.create(
            profile=profile,
            title="Recipe 2",
            host="example.com",
            site_name="Example",
        )
        recipe3 = Recipe.objects.create(
            profile=profile,
            title="Remix Recipe",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
        )
        # Only add one to view history to verify count is total recipes, not history
        RecipeViewHistory.objects.create(profile=profile, recipe=recipe3)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        # Should show "My Recipes (3)" not "View All (1)"
        assert "My Recipes (3)" in content

    def test_home_redirects_on_invalid_profile(self, client):
        """Home redirects if profile in session doesn't exist."""
        # Set invalid profile_id in session
        session = client.session
        session["profile_id"] = 99999
        session.save()

        response = client.get("/legacy/home/")
        assert response.status_code == 302
        assert response.url == "/legacy/"


@pytest.mark.django_db
class TestLegacySearch:
    """Tests for the legacy search view."""

    def test_search_redirects_without_profile(self, client):
        """Search redirects to profile selector when no profile in session."""
        response = client.get("/legacy/search/?q=cookies")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_search_renders_with_query(self, client):
        """Search renders and displays the query text."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=chocolate%20cake")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="search"' in content
        assert "chocolate cake" in content

    def test_search_url_query_searches_normally(self, client):
        """Search treats URL queries as normal search (no import card)."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=https://example.com/recipe")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Import Recipe from URL" not in content
        assert "url-import-card" not in content
        assert "source-filters" in content

    def test_search_not_url_mode(self, client):
        """Search shows regular search mode for non-URL queries."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=pasta")
        assert response.status_code == 200
        content = response.content.decode()
        # Should have source filters div (for JS to populate)
        assert "source-filters" in content
        # Should NOT have URL import card
        assert "url-import-card" not in content

    def test_search_has_nav_header(self, client):
        """Search page has navigation header with link to home."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=test")
        assert response.status_code == 200
        content = response.content.decode()
        # Nav header includes the Cookie logo/title that links home
        assert "header-title" in content
        assert "Cookie" in content

    def test_search_has_search_bar(self, client):
        """Search results page has search bar for new searches."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=pasta")
        assert response.status_code == 200
        content = response.content.decode()
        # Search bar should be present with the query value
        assert 'id="search-form"' in content
        assert 'id="search-input"' in content
        assert 'value="pasta"' in content

    def test_search_empty_query(self, client):
        """Search handles empty query gracefully."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="search"' in content


@pytest.mark.django_db
class TestLegacyNavHeader:
    """Tests for the persistent navigation header (shared base template partial)."""

    def test_nav_header_has_all_links(self, client):
        """Navigation header includes all expected navigation links."""
        profile = Profile.objects.create(name="Alice", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/home/")
        assert response.status_code == 200
        content = response.content.decode()
        # Structure
        assert "header-title" in content
        assert "header-nav" in content
        assert "Cookie" in content
        # All nav links present
        assert 'aria-label="Home"' in content
        assert 'aria-label="Favorites"' in content
        assert 'aria-label="Collections"' in content
        assert 'aria-label="Settings"' in content
        # Profile initial and logout
        assert "logout-btn" in content
        assert ">A<" in content


@pytest.mark.django_db
class TestLegacyTemplateRendering:
    """Tests for legacy template rendering and structure."""

    def test_base_template_includes_css(self, client):
        """Base template includes all required CSS files."""
        response = client.get("/legacy/")
        content = response.content.decode()
        assert "legacy/css/base.css" in content
        assert "legacy/css/components.css" in content
        assert "legacy/css/layout.css" in content

    def test_base_template_includes_js(self, client):
        """Base template includes all required JS files."""
        response = client.get("/legacy/")
        content = response.content.decode()
        assert "legacy/js/polyfills.js" in content
        assert "legacy/js/ajax.js" in content
        assert "legacy/js/state.js" in content
        assert "legacy/js/toast.js" in content
        assert "legacy/js/app.js" in content

    def test_base_template_has_toast_container(self, client):
        """Base template includes toast notification container."""
        response = client.get("/legacy/")
        content = response.content.decode()
        assert "toast-container" in content

    def test_home_includes_page_js(self, client):
        """Home page includes its specific JS file."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/home/")
        content = response.content.decode()
        assert "legacy/js/pages/home.js" in content

    def test_search_includes_page_js(self, client):
        """Search page includes its specific JS file."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/search/?q=test")
        content = response.content.decode()
        assert "legacy/js/pages/search.js" in content

    def test_profile_selector_includes_page_js(self, client):
        """Profile selector includes its specific JS file."""
        response = client.get("/legacy/")
        content = response.content.decode()
        assert "legacy/js/pages/profile-selector.js" in content
