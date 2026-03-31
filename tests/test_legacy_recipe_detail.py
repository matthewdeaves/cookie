"""Tests for Legacy recipe detail view and recipe card rendering."""

from unittest.mock import patch

import pytest

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeFavorite,
    RecipeViewHistory,
)


@pytest.mark.django_db
class TestLegacyRecipeCard:
    """Tests for the recipe card partial rendering."""

    def test_recipe_card_shows_title(self, client):
        """Recipe card displays the recipe title."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Chocolate Chip Cookies",
            host="example.com",
            site_name="Example",
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        assert "Chocolate Chip Cookies" in content

    def test_recipe_card_shows_source(self, client):
        """Recipe card displays the source host."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="allrecipes.com",
            site_name="Allrecipes",
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        host = "allrecipes.com"  # test fixture hostname
        assert host in content

    def test_recipe_card_shows_time(self, client):
        """Recipe card displays total time when available."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            total_time=45,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        assert "45" in content  # Time display

    def test_recipe_card_shows_rating(self, client):
        """Recipe card displays rating when available."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            rating=4.5,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        assert "4.5" in content

    def test_recipe_card_shows_remix_badge(self, client):
        """Recipe card displays remix badge for remixed recipes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Remixed Recipe",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)

        client.post(f"/api/profiles/{profile.id}/select/")
        response = client.get("/legacy/home/")
        content = response.content.decode()
        assert "Remix" in content
        assert "recipe-card-badge" in content


@pytest.mark.django_db
class TestLegacyRecipeDetail:
    """Tests for the legacy recipe detail view."""

    def test_recipe_detail_redirects_without_profile(self, client):
        """Recipe detail redirects to profile selector when no profile in session."""
        profile = Profile.objects.create(name="Temp", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        response = client.get(f"/legacy/recipe/{recipe.id}/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_recipe_detail_renders(self, client):
        """Recipe detail renders successfully with profile."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Chocolate Chip Cookies",
            host="example.com",
            site_name="Example",
            description="Delicious cookies",
            ingredients=["2 cups flour", "1 cup sugar", "1 cup butter"],
            instructions=["Mix ingredients", "Bake at 350F for 10 minutes"],
            rating=4.5,
            rating_count=100,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="recipe-detail"' in content
        assert "Chocolate Chip Cookies" in content

    def test_recipe_detail_shows_all_tabs(self, client):
        """Recipe detail shows all four tabs."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "tab-ingredients" in content
        assert "tab-instructions" in content
        assert "tab-nutrition" in content
        assert "tab-tips" in content

    def test_recipe_detail_shows_ingredients(self, client):
        """Recipe detail displays ingredients list."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            ingredients=["2 cups flour", "1 cup sugar"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "2 cups flour" in content
        assert "1 cup sugar" in content

    def test_recipe_detail_shows_instructions(self, client):
        """Recipe detail displays instructions."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1: Mix", "Step 2: Bake"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "Step 1: Mix" in content
        assert "Step 2: Bake" in content

    def test_recipe_detail_shows_nutrition(self, client):
        """Recipe detail displays nutrition info when available."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            nutrition={"calories": "200", "protein": "5g"},
            servings=4,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "Calories" in content  # format_nutrition_key capitalizes
        assert "200" in content

    def test_recipe_detail_records_view_history(self, client):
        """Recipe detail creates/updates view history."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        assert RecipeViewHistory.objects.count() == 0
        client.get(f"/legacy/recipe/{recipe.id}/")
        assert RecipeViewHistory.objects.count() == 1
        history = RecipeViewHistory.objects.first()
        assert history.profile == profile
        assert history.recipe == recipe

    def test_recipe_detail_shows_favorite_state(self, client):
        """Recipe detail shows correct favorite button state."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        # Check that favorite button has active class
        assert "hero-action-btn active" in content

    def test_recipe_detail_shows_collections(self, client):
        """Recipe detail shows user's collections in modal."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        RecipeCollection.objects.create(profile=profile, name="Weeknight Dinners")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "Weeknight Dinners" in content

    def test_recipe_detail_404_for_nonexistent(self, client):
        """Recipe detail returns 404 for non-existent recipe."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/recipe/99999/")
        assert response.status_code == 404

    def test_recipe_detail_hides_other_remix(self, client):
        """Recipe detail returns 404 when trying to view another user's recipe."""
        profile1 = Profile.objects.create(name="User1", avatar_color="#d97850")
        profile2 = Profile.objects.create(name="User2", avatar_color="#6b8e5f")
        remix = Recipe.objects.create(
            profile=profile2,
            title="Private Remix",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile2,
        )
        client.post(f"/api/profiles/{profile1.id}/select/")

        response = client.get(f"/legacy/recipe/{remix.id}/")
        assert response.status_code == 404  # Recipe not found for this profile

    def test_recipe_detail_shows_own_remix(self, client):
        """Recipe detail shows user's own remix."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        remix = Recipe.objects.create(
            profile=profile,
            title="My Remix",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{remix.id}/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "My Remix" in content

    def test_recipe_detail_includes_css_and_js(self, client):
        """Recipe detail includes page-specific CSS and JS."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "legacy/css/recipe-detail.css" in content
        # Detail page now uses modular JS files (Phase 6 refactoring)
        assert "legacy/js/pages/detail-core.js" in content
        assert "legacy/js/pages/detail-init.js" in content

    def test_recipe_detail_shows_linked_recipes_for_remix(self, client):
        """Recipe detail shows linked recipes when viewing a remix."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        original = Recipe.objects.create(
            profile=profile,
            title="Original Recipe",
            host="example.com",
            site_name="Example",
        )
        remix = Recipe.objects.create(
            profile=profile,
            title="Remix Recipe",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
            remixed_from=original,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{remix.id}/")
        content = response.content.decode()
        assert "linked-recipes-section" in content
        assert "Original Recipe" in content
        assert "(original)" in content

    def test_recipe_detail_shows_linked_recipes_for_original(self, client):
        """Recipe detail shows linked recipes when viewing an original with remixes."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        original = Recipe.objects.create(
            profile=profile,
            title="Original Recipe",
            host="example.com",
            site_name="Example",
        )
        Recipe.objects.create(
            profile=profile,
            title="Remix Recipe",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
            remixed_from=original,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{original.id}/")
        content = response.content.decode()
        assert "linked-recipes-section" in content
        assert "Remix Recipe" in content
        assert "(remix)" in content

    def test_recipe_detail_no_linked_recipes_when_none(self, client):
        """Recipe detail does not show linked recipes section when there are none."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Standalone Recipe",
            host="example.com",
            site_name="Example",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "linked-recipes-section" not in content

    def test_recipe_detail_shows_serving_adjuster_without_ai(self, client):
        """Recipe detail shows static servings when AI not configured."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            servings=4,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        # Should show static servings, not adjuster
        assert "Servings:" in content
        assert "serving-adjuster" not in content  # Adjuster partial not rendered


@pytest.mark.django_db
class TestLegacyRecipeDetailEdgeCases:
    """Tests for edge cases in recipe detail view."""

    def test_recipe_detail_instructions_text_fallback(self, client):
        """Recipe detail falls back to instructions_text when instructions list is empty."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Text Instructions Recipe",
            host="example.com",
            site_name="Example",
            instructions=[],
            instructions_text="Preheat oven\nMix ingredients\nBake for 30 minutes",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/")
        content = response.content.decode()
        assert "Preheat oven" in content
        assert "Mix ingredients" in content

    def test_recipe_detail_shows_sibling_remixes(self, client):
        """Recipe detail shows sibling remixes when viewing a remix."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        original = Recipe.objects.create(
            profile=profile,
            title="Original Recipe",
            host="example.com",
            site_name="Example",
        )
        remix1 = Recipe.objects.create(
            profile=profile,
            title="Remix One",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
            remixed_from=original,
        )
        Recipe.objects.create(
            profile=profile,
            title="Sibling Remix",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile,
            remixed_from=original,
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{remix1.id}/")
        content = response.content.decode()
        assert "Original Recipe" in content
        assert "Sibling Remix" in content
        assert "(sibling)" in content
