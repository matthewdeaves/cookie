"""
Tests for the AI serving adjustment (scaling) service (T045).

Tests apps/ai/services/scaling.py:
- scale_recipe() scaling up and down
- Cached results returned on duplicate request
- Missing servings raises ValueError
- Invalid target servings raises ValueError
- calculate_nutrition() basic calculation
- _parse_time() and _format_time() helpers
"""

from unittest.mock import patch, MagicMock

import pytest

from apps.ai.services.scaling import (
    scale_recipe,
    calculate_nutrition,
    _parse_time,
    _format_time,
)
from apps.profiles.models import Profile
from apps.recipes.models import Recipe, ServingAdjustment


@pytest.fixture
def profile(db):
    """Create a test profile."""
    return Profile.objects.create(name="Test Chef", avatar_color="#d97850")


@pytest.fixture
def recipe(profile, db):
    """Create a test recipe with servings."""
    return Recipe.objects.create(
        profile=profile,
        title="Chocolate Cake",
        host="example.com",
        servings=4,
        ingredients=["2 cups flour", "1 cup sugar", "3 eggs"],
        instructions=["Mix dry ingredients", "Add wet ingredients", "Bake at 350F"],
        prep_time=15,
        cook_time=30,
        total_time=45,
    )


@pytest.fixture
def recipe_no_servings(profile, db):
    """Create a recipe without servings info."""
    return Recipe.objects.create(
        profile=profile,
        title="Mystery Dish",
        host="example.com",
        ingredients=["some stuff"],
    )


@pytest.fixture
def serving_adjustment_prompt(db):
    """Create the serving_adjustment AI prompt."""
    from apps.ai.models import AIPrompt

    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="serving_adjustment",
        defaults={
            "name": "Serving Adjustment",
            "system_prompt": "You are a cooking assistant that scales recipes.",
            "user_prompt_template": (
                "Scale '{title}' from {original_servings} to {new_servings} servings.\n"
                "Ingredients:\n{ingredients}\n"
                "Instructions:\n{instructions}\n"
                "Prep time: {prep_time}\nCook time: {cook_time}\nTotal time: {total_time}"
            ),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


# --- _parse_time ---


class TestParseTime:
    """Tests for _parse_time() helper."""

    def test_minutes(self):
        assert _parse_time("30 minutes") == 30

    def test_hours(self):
        assert _parse_time("2 hours") == 120

    def test_hours_and_minutes(self):
        assert _parse_time("1 hour 30 minutes") == 90

    def test_none(self):
        assert _parse_time(None) is None

    def test_empty_string(self):
        assert _parse_time("") is None

    def test_no_numbers(self):
        assert _parse_time("a few minutes") is None

    def test_case_insensitive(self):
        assert _parse_time("45 Minutes") == 45


# --- _format_time ---


class TestFormatTime:
    """Tests for _format_time() helper."""

    def test_minutes_only(self):
        assert _format_time(30) == "30 minutes"

    def test_one_hour(self):
        assert _format_time(60) == "1 hour"

    def test_hours_plural(self):
        assert _format_time(120) == "2 hours"

    def test_hours_and_minutes(self):
        assert _format_time(90) == "1 hour 30 minutes"

    def test_none(self):
        assert _format_time(None) == "Not specified"

    def test_zero(self):
        assert _format_time(0) == "Not specified"


# --- scale_recipe ---


@pytest.mark.django_db
class TestScaleRecipe:
    """Tests for scale_recipe()."""

    def test_missing_servings_raises(self, recipe_no_servings, profile):
        with pytest.raises(ValueError, match="serving information"):
            scale_recipe(recipe_no_servings.id, 4, profile)

    def test_invalid_target_raises(self, recipe, profile):
        with pytest.raises(ValueError, match="at least 1"):
            scale_recipe(recipe.id, 0, profile)

    def test_nonexistent_recipe_raises(self, profile):
        with pytest.raises(Recipe.DoesNotExist):
            scale_recipe(99999, 4, profile)

    @patch("apps.ai.services.scaling.AIResponseValidator")
    @patch("apps.ai.services.scaling.OpenRouterService")
    def test_scale_up(self, mock_service_cls, mock_validator_cls, recipe, profile, serving_adjustment_prompt):
        """Scaling from 4 to 8 servings."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = {
            "ingredients": ["4 cups flour", "2 cups sugar", "6 eggs"],
            "instructions": ["Mix dry ingredients", "Add wet ingredients", "Bake at 350F"],
            "notes": ["Double all quantities"],
            "prep_time": "20 minutes",
            "cook_time": "45 minutes",
            "total_time": "1 hour 5 minutes",
        }

        result = scale_recipe(recipe.id, 8, profile)

        assert result["target_servings"] == 8
        assert result["original_servings"] == 4
        assert result["cached"] is False
        assert len(result["ingredients"]) == 3
        assert result["notes"] == ["Double all quantities"]
        assert result["prep_time_adjusted"] == 20
        assert result["cook_time_adjusted"] == 45
        assert result["total_time_adjusted"] == 65

    @patch("apps.ai.services.scaling.AIResponseValidator")
    @patch("apps.ai.services.scaling.OpenRouterService")
    def test_scale_down(self, mock_service_cls, mock_validator_cls, recipe, profile, serving_adjustment_prompt):
        """Scaling from 4 to 2 servings."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = {
            "ingredients": ["1 cup flour", "0.5 cup sugar", "1.5 eggs"],
            "instructions": ["Mix dry ingredients", "Add wet ingredients", "Bake at 350F"],
            "notes": ["Halve all quantities"],
        }

        result = scale_recipe(recipe.id, 2, profile)

        assert result["target_servings"] == 2
        assert result["original_servings"] == 4
        assert result["cached"] is False
        # tidy_quantities should convert 0.5 to 1/2
        assert any("1/2" in ing for ing in result["ingredients"])

    @patch("apps.ai.services.scaling.AIResponseValidator")
    @patch("apps.ai.services.scaling.OpenRouterService")
    def test_cached_result_returned(
        self, mock_service_cls, mock_validator_cls, recipe, profile, serving_adjustment_prompt
    ):
        """Pre-cached results are returned without calling AI."""
        # Create cached adjustment
        ServingAdjustment.objects.create(
            recipe=recipe,
            profile=profile,
            target_servings=8,
            unit_system="metric",
            ingredients=["4 cups flour", "2 cups sugar"],
            instructions=["Mix everything"],
            notes=["Doubled"],
            prep_time_adjusted=20,
            cook_time_adjusted=45,
            total_time_adjusted=65,
        )

        result = scale_recipe(recipe.id, 8, profile)

        assert result["cached"] is True
        assert result["target_servings"] == 8
        assert result["ingredients"] == ["4 cups flour", "2 cups sugar"]
        assert result["instructions"] == ["Mix everything"]
        assert result["prep_time_adjusted"] == 20
        # AI should NOT have been called
        mock_service_cls.assert_not_called()

    @patch("apps.ai.services.scaling.AIResponseValidator")
    @patch("apps.ai.services.scaling.OpenRouterService")
    def test_creates_cache_entry(
        self, mock_service_cls, mock_validator_cls, recipe, profile, serving_adjustment_prompt
    ):
        """Successful scaling creates a ServingAdjustment cache entry."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = {
            "ingredients": ["6 cups flour"],
            "instructions": ["Mix"],
            "notes": [],
        }

        scale_recipe(recipe.id, 6, profile)

        assert ServingAdjustment.objects.filter(
            recipe=recipe,
            profile=profile,
            target_servings=6,
        ).exists()


# --- calculate_nutrition ---


class TestCalculateNutrition:
    """Tests for calculate_nutrition()."""

    def test_no_nutrition_data(self):
        recipe = MagicMock()
        recipe.nutrition = {}
        result = calculate_nutrition(recipe, 4, 8)
        assert result == {"per_serving": {}, "total": {}}

    def test_none_nutrition(self):
        recipe = MagicMock()
        recipe.nutrition = None
        # nutrition is falsy
        result = calculate_nutrition(recipe, 4, 8)
        assert result == {"per_serving": {}, "total": {}}

    def test_numeric_values_scaled(self):
        recipe = MagicMock()
        recipe.nutrition = {"calories": 250, "protein": 10.5}
        result = calculate_nutrition(recipe, 4, 8)

        assert result["per_serving"] == {"calories": 250, "protein": 10.5}
        assert result["total"]["calories"] == 250 * 8
        assert result["total"]["protein"] == 10.5 * 8

    def test_string_values_with_units(self):
        recipe = MagicMock()
        recipe.nutrition = {"calories": "250 kcal", "fat": "12.5 g"}
        result = calculate_nutrition(recipe, 4, 2)

        assert result["per_serving"] == {"calories": "250 kcal", "fat": "12.5 g"}
        assert result["total"]["calories"] == "500 kcal"
        assert result["total"]["fat"] == "25 g"

    def test_string_values_without_numbers(self):
        """Non-numeric string values pass through."""
        recipe = MagicMock()
        recipe.nutrition = {"note": "varies by serving"}
        result = calculate_nutrition(recipe, 4, 8)
        assert result["total"]["note"] == "varies by serving"

    def test_integer_total_formatted_cleanly(self):
        """Whole number totals don't show decimal."""
        recipe = MagicMock()
        recipe.nutrition = {"calories": "100 kcal"}
        result = calculate_nutrition(recipe, 1, 3)
        assert result["total"]["calories"] == "300 kcal"

    def test_per_serving_unchanged(self):
        """Per-serving values are always the original nutrition."""
        recipe = MagicMock()
        recipe.nutrition = {"calories": 200}
        result = calculate_nutrition(recipe, 4, 12)
        assert result["per_serving"]["calories"] == 200
