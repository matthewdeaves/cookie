"""
Tests for the AI recipe remix service (T046).

Tests apps/ai/services/remix.py:
- get_remix_suggestions() with valid recipe
- create_remix() with mocked AI response
- Error for non-existent recipe
- _parse_time() and _parse_servings() helpers
- estimate_nutrition() with mocked AI
"""

from unittest.mock import patch, MagicMock

import pytest

from apps.ai.services.remix import (
    get_remix_suggestions,
    create_remix,
    estimate_nutrition,
    _parse_time,
    _parse_servings,
)
from apps.ai.services.openrouter import AIUnavailableError, AIResponseError
from apps.profiles.models import Profile
from apps.recipes.models import Recipe


@pytest.fixture
def profile(db):
    """Create a test profile."""
    return Profile.objects.create(name="Remix Chef", avatar_color="#d97850")


@pytest.fixture
def recipe(profile, db):
    """Create a test recipe for remixing."""
    return Recipe.objects.create(
        profile=profile,
        title="Classic Chocolate Cake",
        host="example.com",
        description="A rich chocolate cake",
        ingredients=["2 cups flour", "1 cup sugar", "1/2 cup cocoa", "3 eggs"],
        instructions=["Mix dry ingredients", "Add wet ingredients", "Bake at 350F for 30 min"],
        instructions_text="Mix dry ingredients\nAdd wet ingredients\nBake at 350F for 30 min",
        cuisine="American",
        category="Dessert",
        servings=8,
        nutrition={"calories": "350 kcal", "fat": "12 g", "protein": "5 g"},
    )


@pytest.fixture
def remix_suggestions_prompt(db):
    """Create the remix_suggestions AI prompt."""
    from apps.ai.models import AIPrompt

    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="remix_suggestions",
        defaults={
            "name": "Remix Suggestions",
            "system_prompt": "You suggest recipe variations.",
            "user_prompt_template": (
                "Suggest 6 remixes for '{title}'.\n"
                "Cuisine: {cuisine}\nCategory: {category}\n"
                "Ingredients:\n{ingredients}"
            ),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def recipe_remix_prompt(db):
    """Create the recipe_remix AI prompt."""
    from apps.ai.models import AIPrompt

    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="recipe_remix",
        defaults={
            "name": "Recipe Remix",
            "system_prompt": "You create recipe variations.",
            "user_prompt_template": (
                "Remix '{title}' with modification: {modification}\n"
                "Description: {description}\n"
                "Ingredients:\n{ingredients}\n"
                "Instructions:\n{instructions}"
            ),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def nutrition_estimate_prompt(db):
    """Create the nutrition_estimate AI prompt."""
    from apps.ai.models import AIPrompt

    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="nutrition_estimate",
        defaults={
            "name": "Nutrition Estimate",
            "system_prompt": "You estimate nutrition values.",
            "user_prompt_template": (
                "Original nutrition:\n{original_nutrition}\n"
                "Original ingredients:\n{original_ingredients}\n"
                "Original servings: {original_servings}\n"
                "New ingredients:\n{new_ingredients}\n"
                "New servings: {new_servings}\n"
                "Modification: {modification}"
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
        assert _parse_time("1 hour 15 minutes") == 75

    def test_none(self):
        assert _parse_time(None) is None

    def test_empty(self):
        assert _parse_time("") is None

    def test_no_number(self):
        assert _parse_time("some time") is None


# --- _parse_servings ---


class TestParseServings:
    """Tests for _parse_servings() helper."""

    def test_servings_string(self):
        assert _parse_servings("4 servings") == 4

    def test_plain_number(self):
        assert _parse_servings("6") == 6

    def test_empty(self):
        assert _parse_servings("") is None

    def test_none(self):
        """None input returns None."""
        # _parse_servings checks `if not yields_str` so None should be caught
        assert _parse_servings(None) is None

    def test_no_number(self):
        assert _parse_servings("a few") is None


# --- get_remix_suggestions ---


@pytest.mark.django_db
class TestGetRemixSuggestions:
    """Tests for get_remix_suggestions()."""

    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_valid_recipe(self, mock_service_cls, mock_validator_cls, recipe, remix_suggestions_prompt):
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        suggestions = [
            "Make it vegan",
            "Add spicy twist",
            "Gluten-free version",
            "Low-sugar version",
            "Add fruit topping",
            "Mexican chocolate style",
        ]
        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = suggestions

        # Bypass the cache decorator
        with patch("apps.ai.services.remix.cache_ai_response", lambda *a, **kw: lambda f: f):
            # Need to re-import or call the underlying function
            # Since the decorator is applied at import time, we patch the cache instead
            pass

        # The function is already decorated, so we need to patch Django cache
        from django.core.cache import cache

        cache.clear()

        result = get_remix_suggestions(recipe.id)

        assert result == suggestions
        assert len(result) == 6

    def test_nonexistent_recipe_raises(self):
        with pytest.raises(Recipe.DoesNotExist):
            # Clear cache to ensure it hits the DB
            from django.core.cache import cache

            cache.clear()
            get_remix_suggestions(99999)

    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_ai_unavailable(self, mock_service_cls, mock_validator_cls, recipe, remix_suggestions_prompt):
        mock_service_cls.return_value = MagicMock()
        mock_service_cls.return_value.complete.side_effect = AIUnavailableError("No API key")

        from django.core.cache import cache

        cache.clear()

        with pytest.raises(AIUnavailableError):
            get_remix_suggestions(recipe.id)


# --- create_remix ---


@pytest.mark.django_db
class TestCreateRemix:
    """Tests for create_remix()."""

    @patch("apps.ai.services.remix._generate_tips_background")
    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_creates_remix_recipe(
        self,
        mock_service_cls,
        mock_validator_cls,
        mock_tips_bg,
        recipe,
        profile,
        recipe_remix_prompt,
    ):
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = {
            "title": "Vegan Chocolate Cake",
            "description": "A plant-based chocolate cake",
            "ingredients": ["2 cups flour", "1 cup sugar", "1/2 cup cocoa", "flax eggs"],
            "instructions": ["Mix dry", "Add wet", "Bake at 350F"],
            "prep_time": "20 minutes",
            "cook_time": "35 minutes",
            "total_time": "55 minutes",
            "yields": "8 servings",
        }

        remix = create_remix(recipe.id, "Make it vegan", profile)

        assert remix.title == "Vegan Chocolate Cake"
        assert remix.is_remix is True
        assert remix.host == "user-generated"
        assert remix.site_name == "User Generated"
        assert remix.source_url is None
        assert remix.remixed_from_id == recipe.id
        assert remix.profile == profile
        assert remix.remix_profile == profile
        assert remix.prep_time == 20
        assert remix.cook_time == 35
        assert remix.total_time == 55
        assert remix.servings == 8
        assert remix.cuisine == recipe.cuisine  # Carried over
        assert remix.category == recipe.category  # Carried over
        assert len(remix.ingredients) == 4
        assert len(remix.instructions) == 3

    @patch("apps.ai.services.remix._generate_tips_background")
    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_remix_with_nutrition_estimation(
        self,
        mock_service_cls,
        mock_validator_cls,
        mock_tips_bg,
        recipe,
        profile,
        recipe_remix_prompt,
        nutrition_estimate_prompt,
    ):
        """When original has nutrition, estimate_nutrition is called."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        # First call: recipe_remix, second call: nutrition_estimate
        call_count = {"n": 0}
        remix_response = {
            "title": "Light Chocolate Cake",
            "description": "Lower calorie version",
            "ingredients": ["1 cup flour", "1/2 cup sugar"],
            "instructions": ["Mix", "Bake"],
            "yields": "8 servings",
        }
        nutrition_response = {"calories": "200 kcal", "fat": "6 g"}

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance

        def validate_side_effect(prompt_type, response):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return remix_response
            return nutrition_response

        mock_validator_instance.validate.side_effect = validate_side_effect

        remix = create_remix(recipe.id, "Make it lighter", profile)

        # Nutrition should have been estimated and saved
        remix.refresh_from_db()
        assert remix.nutrition == {"calories": "200 kcal", "fat": "6 g"}

    def test_nonexistent_recipe_raises(self, profile):
        with pytest.raises(Recipe.DoesNotExist):
            create_remix(99999, "Make it vegan", profile)

    @patch("apps.ai.services.remix._generate_tips_background")
    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_remix_without_times(
        self,
        mock_service_cls,
        mock_validator_cls,
        mock_tips_bg,
        recipe,
        profile,
        recipe_remix_prompt,
    ):
        """Remix response without time fields results in None times."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = {
            "title": "Quick Cake",
            "description": "Fast version",
            "ingredients": ["flour", "sugar"],
            "instructions": ["Mix", "Bake"],
            "yields": "",
        }

        remix = create_remix(recipe.id, "Make it quicker", profile)

        assert remix.prep_time is None
        assert remix.cook_time is None
        assert remix.total_time is None
        assert remix.servings is None


# --- estimate_nutrition ---


@pytest.mark.django_db
class TestEstimateNutrition:
    """Tests for estimate_nutrition()."""

    @patch("apps.ai.services.remix.AIResponseValidator")
    @patch("apps.ai.services.remix.OpenRouterService")
    def test_returns_validated_nutrition(self, mock_service_cls, mock_validator_cls, recipe, nutrition_estimate_prompt):
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.complete.return_value = "mocked"

        expected = {"calories": "300 kcal", "fat": "10 g", "protein": "6 g"}
        mock_validator_instance = MagicMock()
        mock_validator_cls.return_value = mock_validator_instance
        mock_validator_instance.validate.return_value = expected

        result = estimate_nutrition(
            original=recipe,
            new_ingredients=["2 cups flour", "1 cup sugar"],
            new_servings=8,
            modification="Make it healthier",
        )

        assert result == expected
        mock_service_instance.complete.assert_called_once()
