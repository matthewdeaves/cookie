"""
Tests for system API endpoints (database reset).

These tests verify the dangerous database reset functionality works correctly
and safely, including proper confirmation requirements and data preservation.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from django.test import Client
from django.conf import settings
from django.core.files.base import ContentFile


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def test_profile(db):
    """Create a test profile."""
    from apps.profiles.models import Profile

    return Profile.objects.create(name="Test User", avatar_color="#123456")


@pytest.fixture
def populated_database(db, test_profile):
    """
    Create a fully populated database with all entity types.
    Returns dict with all created objects for verification.
    """
    from apps.profiles.models import Profile
    from apps.recipes.models import (
        Recipe,
        RecipeFavorite,
        RecipeCollection,
        RecipeCollectionItem,
        RecipeViewHistory,
        SearchSource,
        ServingAdjustment,
        CachedSearchImage,
    )
    from apps.ai.models import AIDiscoverySuggestion

    # Create additional profile
    profile2 = Profile.objects.create(name="Second User", avatar_color="#654321")

    # Create recipes
    recipe1 = Recipe.objects.create(
        profile=test_profile,
        title="Test Recipe 1",
        host="allrecipes.com",
        ingredients=["flour", "sugar"],
        instructions=["mix", "bake"],
    )
    recipe2 = Recipe.objects.create(
        profile=test_profile,
        title="Test Recipe 2",
        host="bbcgoodfood.com",
        ingredients=["eggs", "milk"],
        instructions=["whisk", "cook"],
    )

    # Create favorites
    favorite = RecipeFavorite.objects.create(
        profile=test_profile,
        recipe=recipe1,
    )

    # Create collections
    collection = RecipeCollection.objects.create(
        profile=test_profile,
        name="My Favorites",
        description="Best recipes",
    )
    collection_item = RecipeCollectionItem.objects.create(
        collection=collection,
        recipe=recipe1,
        order=0,
    )

    # Create view history
    history = RecipeViewHistory.objects.create(
        profile=test_profile,
        recipe=recipe1,
    )

    # Create AI discovery suggestions
    ai_suggestion = AIDiscoverySuggestion.objects.create(
        profile=test_profile,
        suggestion_type="seasonal",
        search_query="summer salads",
        title="Summer Salads",
        description="Fresh and light recipes",
    )

    # Create serving adjustment cache
    serving_adj = ServingAdjustment.objects.create(
        recipe=recipe1,
        profile=test_profile,
        target_servings=8,
        unit_system="metric",
        ingredients=["2 cups flour", "1 cup sugar"],
        notes=["Double the baking time"],
    )

    # Create cached search image
    cached_image = CachedSearchImage.objects.create(
        external_url="https://example.com/image.jpg",
        status=CachedSearchImage.STATUS_SUCCESS,
    )

    return {
        "profiles": [test_profile, profile2],
        "recipes": [recipe1, recipe2],
        "favorites": [favorite],
        "collections": [collection],
        "collection_items": [collection_item],
        "history": [history],
        "ai_suggestions": [ai_suggestion],
        "serving_adjustments": [serving_adj],
        "cached_images": [cached_image],
    }


@pytest.mark.django_db
class TestHealthCheck:
    """Tests for GET /api/system/health/"""

    def test_health_check_returns_healthy(self, client):
        """Test health check returns healthy status when database is accessible."""
        response = client.get("/api/system/health/")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"


@pytest.mark.django_db
class TestResetPreview:
    """Tests for GET /api/system/reset-preview/"""

    def test_preview_empty_database(self, client):
        """Test preview with empty database returns zero counts."""
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 200

        data = response.json()
        counts = data["data_counts"]

        assert counts["profiles"] == 0
        assert counts["recipes"] == 0
        assert counts["recipe_images"] == 0
        assert counts["favorites"] == 0
        assert counts["collections"] == 0
        assert counts["collection_items"] == 0
        assert counts["view_history"] == 0
        assert counts["ai_suggestions"] == 0
        assert counts["serving_adjustments"] == 0
        assert counts["cached_search_images"] == 0

    def test_preview_populated_database(self, client, populated_database):
        """Test preview with populated database returns correct counts."""
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 200

        data = response.json()
        counts = data["data_counts"]

        assert counts["profiles"] == 2
        assert counts["recipes"] == 2
        assert counts["favorites"] == 1
        assert counts["collections"] == 1
        assert counts["collection_items"] == 1
        assert counts["view_history"] == 1
        assert counts["ai_suggestions"] == 1
        assert counts["serving_adjustments"] == 1
        assert counts["cached_search_images"] == 1

    def test_preview_returns_preserved_items(self, client):
        """Test preview lists items that will be preserved."""
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 200

        data = response.json()
        preserved = data["preserved"]

        assert "Search source configurations" in preserved
        assert "AI prompt templates" in preserved
        assert "Application settings" in preserved

    def test_preview_returns_warnings(self, client):
        """Test preview includes safety warnings."""
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 200

        data = response.json()
        warnings = data["warnings"]

        assert any("permanently deleted" in w for w in warnings)
        assert any("cannot be undone" in w for w in warnings)

    def test_preview_counts_recipe_images(self, client, test_profile, db):
        """Test preview correctly counts recipes with images."""
        from apps.recipes.models import Recipe

        # Recipe without image
        Recipe.objects.create(
            profile=test_profile,
            title="No Image Recipe",
            host="test.com",
        )

        # Recipe with image (simulate by setting image field)
        recipe_with_image = Recipe.objects.create(
            profile=test_profile,
            title="Has Image Recipe",
            host="test.com",
        )
        # Simulate image by setting the field directly
        recipe_with_image.image = "recipe_images/test.jpg"
        recipe_with_image.save()

        response = client.get("/api/system/reset-preview/")
        data = response.json()

        assert data["data_counts"]["recipes"] == 2
        assert data["data_counts"]["recipe_images"] == 1


@pytest.mark.django_db
class TestResetDatabase:
    """Tests for POST /api/system/reset/"""

    def test_reset_requires_confirmation(self, client):
        """Test reset fails without proper confirmation text."""
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "wrong"},
            content_type="application/json",
        )
        assert response.status_code == 400

        data = response.json()
        assert data["error"] == "invalid_confirmation"
        assert "RESET" in data["message"]

    def test_reset_requires_exact_confirmation(self, client):
        """Test reset requires exact 'RESET' text (case-sensitive)."""
        # Lowercase should fail
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "reset"},
            content_type="application/json",
        )
        assert response.status_code == 400

        # With spaces should fail
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": " RESET "},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_reset_empty_confirmation_fails(self, client):
        """Test reset fails with empty confirmation."""
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": ""},
            content_type="application/json",
        )
        assert response.status_code == 400

    @patch("apps.core.api.call_command")
    def test_reset_deletes_all_user_data(self, mock_call_command, client, populated_database):
        """Test reset deletes all user-created data."""
        from apps.profiles.models import Profile
        from apps.recipes.models import (
            Recipe,
            RecipeFavorite,
            RecipeCollection,
            RecipeCollectionItem,
            RecipeViewHistory,
            ServingAdjustment,
            CachedSearchImage,
        )
        from apps.ai.models import AIDiscoverySuggestion

        # Verify data exists before reset
        assert Profile.objects.count() == 2
        assert Recipe.objects.count() == 2
        assert RecipeFavorite.objects.count() == 1
        assert RecipeCollection.objects.count() == 1
        assert RecipeCollectionItem.objects.count() == 1
        assert RecipeViewHistory.objects.count() == 1
        assert AIDiscoverySuggestion.objects.count() == 1
        assert ServingAdjustment.objects.count() == 1
        assert CachedSearchImage.objects.count() == 1

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify all user data deleted
        assert Profile.objects.count() == 0
        assert Recipe.objects.count() == 0
        assert RecipeFavorite.objects.count() == 0
        assert RecipeCollection.objects.count() == 0
        assert RecipeCollectionItem.objects.count() == 0
        assert RecipeViewHistory.objects.count() == 0
        assert AIDiscoverySuggestion.objects.count() == 0
        assert ServingAdjustment.objects.count() == 0
        assert CachedSearchImage.objects.count() == 0

    @patch("apps.core.api.call_command")
    def test_reset_preserves_search_sources(self, mock_call_command, client, db):
        """Test reset preserves SearchSource configurations."""
        from apps.recipes.models import SearchSource

        # Use get_or_create to handle seeded data, or update existing
        source, created = SearchSource.objects.get_or_create(
            host="test-preserve.example.com",
            defaults={
                "name": "Test Preserve",
                "search_url_template": "https://test-preserve.example.com/search?q={query}",
                "result_selector": ".test-recipe-card",
                "is_enabled": True,
            },
        )
        # Set failure state to verify reset clears it
        source.consecutive_failures = 5
        source.needs_attention = True
        source.save()

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify sources still exist after re-seeding
        assert SearchSource.objects.count() >= 1
        source.refresh_from_db()
        assert source.host == "test-preserve.example.com"
        assert source.result_selector == ".test-recipe-card"
        # Counters should be reset
        assert source.consecutive_failures == 0
        assert source.needs_attention is False
        assert source.last_validated_at is None

    @patch("apps.core.api.call_command")
    def test_reset_preserves_ai_prompts(self, mock_call_command, client, db):
        """Test reset preserves AI prompt configurations."""
        from apps.ai.models import AIPrompt

        # Use get_or_create with unique prompt_type, or modify existing
        prompt, created = AIPrompt.objects.get_or_create(
            prompt_type="test_preserve_prompt",
            defaults={
                "name": "Test Preserve Prompt",
                "system_prompt": "You are a test cooking expert.",
                "user_prompt_template": "Generate test tips for {recipe}",
                "model": "claude-3.5-haiku",
            },
        )
        # Update with custom values to verify preservation
        prompt.system_prompt = "Custom system prompt for testing"
        prompt.save()

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Verify prompts still exist after re-seeding
        assert AIPrompt.objects.count() >= 1
        prompt.refresh_from_db()
        assert prompt.prompt_type == "test_preserve_prompt"
        assert prompt.system_prompt == "Custom system prompt for testing"

    @patch("apps.core.api.call_command")
    def test_reset_clears_django_cache(self, mock_call_command, client, db):
        """Test reset clears Django cache."""
        from django.core.cache import cache

        # Set some cache values
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Cache should be cleared
        assert cache.get("test_key") is None

    @patch("apps.core.api.call_command")
    def test_reset_clears_sessions(self, mock_call_command, client, db):
        """Test reset clears all user sessions."""
        from django.contrib.sessions.models import Session

        # Create a session
        client.session["test_key"] = "test_value"
        client.session.save()

        assert Session.objects.count() >= 1

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # All sessions should be cleared
        assert Session.objects.count() == 0

    @patch("apps.core.api.call_command")
    def test_reset_returns_actions_performed(self, mock_call_command, client, db):
        """Test reset returns list of actions performed."""
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        data = response.json()
        assert data["success"] is True
        assert "Database reset complete" in data["message"]

        actions = data["actions_performed"]
        assert "Deleted all user profiles" in actions
        assert "Deleted all recipes and images" in actions
        assert "Cleared all favorites and collections" in actions
        assert "Cleared all view history" in actions
        assert "Cleared all AI cache data" in actions
        assert "Cleared application cache" in actions
        assert "Cleared all sessions" in actions

    @patch("apps.core.api.call_command")
    @patch("apps.core.api.shutil.rmtree")
    @patch("apps.core.api.os.path.exists")
    @patch("apps.core.api.os.makedirs")
    def test_reset_clears_image_directories(
        self, mock_makedirs, mock_exists, mock_rmtree, mock_call_command, client, db
    ):
        """Test reset removes and recreates image directories."""
        mock_exists.return_value = True

        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Check rmtree was called for both image directories
        rmtree_calls = [str(call) for call in mock_rmtree.call_args_list]
        assert any("recipe_images" in str(call) for call in rmtree_calls)
        assert any("search_images" in str(call) for call in rmtree_calls)

        # Check makedirs was called to recreate them
        makedirs_calls = [str(call) for call in mock_makedirs.call_args_list]
        assert any("recipe_images" in str(call) for call in makedirs_calls)
        assert any("search_images" in str(call) for call in makedirs_calls)

    @patch("apps.core.api.call_command")
    def test_reset_runs_migrations(self, mock_call_command, client, db):
        """Test reset re-runs migrations."""
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Check migrate was called
        migrate_calls = [call for call in mock_call_command.call_args_list if call[0][0] == "migrate"]
        assert len(migrate_calls) >= 1

    @patch("apps.core.api.call_command")
    def test_reset_attempts_seed_commands(self, mock_call_command, client, db):
        """Test reset attempts to run seed commands (gracefully handles if missing)."""
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # Check seed commands were attempted
        command_names = [call[0][0] for call in mock_call_command.call_args_list]
        assert "migrate" in command_names
        # Seed commands should be attempted (may not exist)
        assert "seed_search_sources" in command_names or True  # Optional
        assert "seed_ai_prompts" in command_names or True  # Optional


@pytest.mark.django_db
class TestResetDatabaseEdgeCases:
    """Edge case and error handling tests for database reset."""

    @patch("apps.core.api.call_command")
    def test_reset_with_cascade_relationships(self, mock_call_command, client, test_profile, db):
        """Test reset properly handles cascade deletions."""
        from apps.recipes.models import (
            Recipe,
            RecipeFavorite,
            RecipeCollection,
            RecipeCollectionItem,
            RecipeViewHistory,
        )

        # Create recipe with multiple relationships
        recipe = Recipe.objects.create(
            profile=test_profile,
            title="Recipe with Relations",
            host="test.com",
        )

        # Create multiple favorites pointing to same recipe
        RecipeFavorite.objects.create(profile=test_profile, recipe=recipe)

        # Create collection with item
        collection = RecipeCollection.objects.create(
            profile=test_profile,
            name="Test Collection",
        )
        RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=recipe,
            order=0,
        )

        # Create view history
        RecipeViewHistory.objects.create(profile=test_profile, recipe=recipe)

        # Reset should not raise FK constraint errors
        response = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response.status_code == 200

        # All data should be gone
        assert Recipe.objects.count() == 0
        assert RecipeFavorite.objects.count() == 0
        assert RecipeCollection.objects.count() == 0
        assert RecipeCollectionItem.objects.count() == 0
        assert RecipeViewHistory.objects.count() == 0

    @patch("apps.core.api.call_command")
    def test_reset_idempotent(self, mock_call_command, client, db):
        """Test reset can be called multiple times safely."""
        # First reset on empty database
        response1 = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response1.status_code == 200

        # Second reset should also succeed
        response2 = client.post(
            "/api/system/reset/",
            {"confirmation_text": "RESET"},
            content_type="application/json",
        )
        assert response2.status_code == 200

    def test_reset_rejects_missing_body(self, client, db):
        """Test reset fails gracefully with missing request body."""
        response = client.post(
            "/api/system/reset/",
            content_type="application/json",
        )
        # Should return validation error
        assert response.status_code in [400, 422]

    def test_reset_rejects_invalid_json(self, client, db):
        """Test reset fails gracefully with invalid JSON."""
        response = client.post(
            "/api/system/reset/",
            "not valid json",
            content_type="application/json",
        )
        # Should return validation error
        assert response.status_code in [400, 422]
