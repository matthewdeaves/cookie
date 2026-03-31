"""Tests for Legacy all-recipes, favorites, collections, and collection detail views."""

import pytest

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeFavorite,
)


@pytest.mark.django_db
class TestLegacyAllRecipes:
    """Tests for the legacy all_recipes (My Recipes) view."""

    def test_all_recipes_redirects_without_profile(self, client):
        """All recipes redirects to profile selector when no profile in session."""
        response = client.get("/legacy/all-recipes/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_all_recipes_renders_with_profile(self, client):
        """All recipes page renders when profile is selected."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="all-recipes"' in content
        assert "My Recipes" in content

    def test_all_recipes_shows_profile_recipes(self, client):
        """All recipes page displays user's recipes (imports and remixes)."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        Recipe.objects.create(
            profile=profile,
            title="Imported Recipe",
            host="example.com",
            site_name="Example",
        )
        Recipe.objects.create(
            profile=profile,
            title="My Remix",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Imported Recipe" in content
        assert "My Remix" in content

    def test_all_recipes_shows_recipe_count(self, client):
        """All recipes page shows correct recipe count."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        for i in range(3):
            Recipe.objects.create(
                profile=profile,
                title=f"Recipe {i}",
                host="example.com",
                site_name="Example",
            )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert "3 recipes" in content

    def test_all_recipes_empty_state(self, client):
        """All recipes page shows empty state when no recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert "No recipes yet" in content
        assert "Import Recipes" in content

    def test_all_recipes_does_not_show_other_profiles_recipes(self, client):
        """All recipes page does not show other profile's recipes."""
        profile1 = Profile.objects.create(name="User1", avatar_color="#d97850")
        profile2 = Profile.objects.create(name="User2", avatar_color="#6b8e5f")
        Recipe.objects.create(
            profile=profile1,
            title="User1 Recipe",
            host="example.com",
            site_name="Example",
        )
        Recipe.objects.create(
            profile=profile2,
            title="User2 Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile1.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert "User1 Recipe" in content
        assert "User2 Recipe" not in content

    def test_all_recipes_shows_remix_without_viewing(self, client):
        """All recipes shows newly created remixes without requiring view history."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        Recipe.objects.create(
            profile=profile,
            title="Just Created Remix",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert "Just Created Remix" in content

    def test_all_recipes_has_back_button(self, client):
        """All recipes page has back button to home."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert "/legacy/home/" in content

    def test_all_recipes_has_filter_input(self, client):
        """All recipes page has filter input when recipes exist."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert 'id="recipe-filter"' in content
        assert 'placeholder="Filter recipes..."' in content

    def test_all_recipes_cards_have_data_attributes(self, client):
        """All recipes page cards have data attributes for filtering."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        Recipe.objects.create(
            profile=profile,
            title="Chocolate Cake",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/all-recipes/")
        content = response.content.decode()
        assert 'data-title="Chocolate Cake"' in content
        assert 'data-host="example.com"' in content


@pytest.mark.django_db
class TestLegacyFavorites:
    """Tests for the legacy favorites view."""

    def test_favorites_redirects_without_profile(self, client):
        """Favorites redirects to profile selector when no profile in session."""
        response = client.get("/legacy/favorites/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_favorites_renders_with_profile(self, client):
        """Favorites page renders when profile is selected."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="favorites"' in content

    def test_favorites_shows_favorite_recipes(self, client):
        """Favorites page displays user's favorited recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="My Favorite Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "My Favorite Recipe" in content

    def test_favorites_shows_recipe_count(self, client):
        """Favorites page shows correct recipe count."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        for i in range(3):
            recipe = Recipe.objects.create(
                profile=profile,
                title=f"Recipe {i}",
                host="example.com",
                site_name="Example",
            )
            RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        content = response.content.decode()
        assert "3 recipes" in content

    def test_favorites_empty_state(self, client):
        """Favorites page shows empty state when no favorites."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        content = response.content.decode()
        assert "No favorites yet" in content
        assert "Discover Recipes" in content

    def test_favorites_includes_js(self, client):
        """Favorites page includes its specific JS file."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        content = response.content.decode()
        assert "pages/favorites.js" in content

    def test_favorites_has_back_button(self, client):
        """Favorites page has back button to home."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/favorites/")
        content = response.content.decode()
        assert "/legacy/home/" in content


@pytest.mark.django_db
class TestLegacyCollections:
    """Tests for the legacy collections list view."""

    def test_collections_redirects_without_profile(self, client):
        """Collections redirects to profile selector when no profile in session."""
        response = client.get("/legacy/collections/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_collections_renders_with_profile(self, client):
        """Collections page renders when profile is selected."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="collections"' in content

    def test_collections_shows_user_collections(self, client):
        """Collections page displays user's collections."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        RecipeCollection.objects.create(profile=profile, name="Weeknight Dinners")
        RecipeCollection.objects.create(profile=profile, name="Holiday Favorites")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "Weeknight Dinners" in content
        assert "Holiday Favorites" in content

    def test_collections_shows_recipe_count(self, client):
        """Collections page shows recipe count for each collection."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test Collection")

        for i in range(2):
            recipe = Recipe.objects.create(
                profile=profile,
                title=f"Recipe {i}",
                host="example.com",
                site_name="Example",
            )
            RecipeCollectionItem.objects.create(collection=collection, recipe=recipe, order=i)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "2 recipes" in content

    def test_collections_empty_state(self, client):
        """Collections page shows empty state when no collections."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "No collections yet" in content
        assert "Create Collection" in content

    def test_collections_has_create_button(self, client):
        """Collections page has create collection button."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "create-collection-btn" in content

    def test_collections_includes_css(self, client):
        """Collections page includes collections.css."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "collections.css" in content

    def test_collections_includes_js(self, client):
        """Collections page includes its specific JS file."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/")
        content = response.content.decode()
        assert "pages/collections.js" in content


@pytest.mark.django_db
class TestLegacyCollectionDetail:
    """Tests for the legacy collection detail view."""

    def test_collection_detail_redirects_without_profile(self, client):
        """Collection detail redirects to profile selector when no profile in session."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test")
        response = client.get(f"/legacy/collections/{collection.id}/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_collection_detail_renders(self, client):
        """Collection detail page renders when profile is selected."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="My Collection")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="collection-detail"' in content
        assert "My Collection" in content

    def test_collection_detail_shows_recipes(self, client):
        """Collection detail shows recipes in the collection."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test Collection")

        recipe = Recipe.objects.create(
            profile=profile,
            title="Recipe in Collection",
            host="example.com",
            site_name="Example",
        )
        RecipeCollectionItem.objects.create(collection=collection, recipe=recipe, order=0)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "Recipe in Collection" in content

    def test_collection_detail_shows_description(self, client):
        """Collection detail shows collection description if present."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(
            profile=profile,
            name="Test Collection",
            description="Quick meals for busy weeknights",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "Quick meals for busy weeknights" in content

    def test_collection_detail_empty_state(self, client):
        """Collection detail shows empty state when no recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Empty Collection")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "No recipes in this collection" in content

    def test_collection_detail_has_delete_button(self, client):
        """Collection detail has delete collection button."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "delete-collection-btn" in content

    def test_collection_detail_has_remove_buttons(self, client):
        """Collection detail has remove recipe buttons."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test")

        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeCollectionItem.objects.create(collection=collection, recipe=recipe, order=0)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "remove-recipe-btn" in content

    def test_collection_detail_404_wrong_profile(self, client):
        """Collection detail returns 404 for another user's collection."""
        profile1 = Profile.objects.create(name="User1", avatar_color="#d97850")
        profile2 = Profile.objects.create(name="User2", avatar_color="#6b8e5f")
        collection = RecipeCollection.objects.create(profile=profile2, name="Private")
        client.post(f"/api/profiles/{profile1.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        assert response.status_code == 404

    def test_collection_detail_404_nonexistent(self, client):
        """Collection detail returns 404 for non-existent collection."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/collections/99999/")
        assert response.status_code == 404

    def test_collection_detail_includes_js(self, client):
        """Collection detail includes its specific JS file."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "pages/collection-detail.js" in content

    def test_collection_detail_includes_css(self, client):
        """Collection detail includes collections.css."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        collection = RecipeCollection.objects.create(profile=profile, name="Test")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/collections/{collection.id}/")
        content = response.content.decode()
        assert "collections.css" in content
