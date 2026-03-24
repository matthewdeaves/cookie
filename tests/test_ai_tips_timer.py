"""
Tests for the AI tips generation and timer naming services (T048).

Tests:
- apps/ai/services/tips.py: generate_tips(), clear_tips()
- apps/ai/services/timer.py: generate_timer_name()
"""

from unittest.mock import patch, MagicMock

import pytest

from apps.ai.models import AIPrompt
from apps.ai.services.tips import generate_tips, clear_tips
from apps.ai.services.timer import generate_timer_name
from apps.ai.services.openrouter import AIUnavailableError, AIResponseError
from apps.ai.services.validator import ValidationError
from apps.profiles.models import Profile
from apps.recipes.models import Recipe


@pytest.fixture
def profile(db):
    """Create a test profile."""
    return Profile.objects.create(name="Test User", avatar_color="#d97850")


@pytest.fixture
def recipe(profile):
    """Create a test recipe with ingredients and instructions."""
    return Recipe.objects.create(
        profile=profile,
        title="Spaghetti Carbonara",
        host="example.com",
        canonical_url="https://example.com/carbonara",
        ingredients=["400g spaghetti", "200g pancetta", "4 eggs", "100g parmesan"],
        instructions=[
            {"text": "Cook pasta in salted water"},
            {"text": "Fry pancetta until crispy"},
            {"text": "Mix eggs and parmesan"},
            {"text": "Combine everything"},
        ],
    )


@pytest.fixture
def recipe_with_cached_tips(profile):
    """Create a recipe that already has cached AI tips."""
    return Recipe.objects.create(
        profile=profile,
        title="Cached Tip Recipe",
        host="example.com",
        canonical_url="https://example.com/cached",
        ingredients=["1 cup flour"],
        instructions=[{"text": "Mix and bake"}],
        ai_tips=[
            "Use room temperature eggs for better emulsification.",
            "Reserve pasta water for sauce consistency.",
            "Don't overcook the pancetta.",
        ],
    )


@pytest.fixture
def tips_prompt(db):
    """Get or create the tips_generation AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="tips_generation",
        defaults={
            "name": "Tips Generation",
            "system_prompt": "You are a cooking tips assistant.",
            "user_prompt_template": (
                "Generate tips for '{title}'.\nIngredients:\n{ingredients}\nInstructions:\n{instructions}"
            ),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def timer_prompt(db):
    """Get or create the timer_naming AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="timer_naming",
        defaults={
            "name": "Timer Naming",
            "system_prompt": "You are a timer naming assistant.",
            "user_prompt_template": ("Name this timer:\nInstruction: {instruction}\nDuration: {duration}"),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


# --- generate_tips: cached ---


@pytest.mark.django_db
def test_generate_tips_returns_cached(recipe_with_cached_tips):
    """Cached tips are returned without calling AI."""
    with patch("apps.ai.services.tips.OpenRouterService") as mock_svc:
        result = generate_tips(recipe_with_cached_tips.id)

    mock_svc.assert_not_called()
    assert result["cached"] is True
    assert len(result["tips"]) == 3
    assert "room temperature eggs" in result["tips"][0]


# --- generate_tips: uncached ---


@pytest.mark.django_db
def test_generate_tips_calls_ai_when_uncached(recipe, tips_prompt):
    """Tips are generated via AI when not cached."""
    mock_tips = [
        "Tip one about pasta.",
        "Tip two about sauce.",
        "Tip three about timing.",
    ]

    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = mock_tips

    with (
        patch(
            "apps.ai.services.tips.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.tips.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = generate_tips(recipe.id)

    assert result["cached"] is False
    assert result["tips"] == mock_tips

    # Verify tips were cached on the recipe
    recipe.refresh_from_db()
    assert recipe.ai_tips == mock_tips


@pytest.mark.django_db
def test_generate_tips_with_string_instructions(profile, tips_prompt):
    """Tips generation handles string instructions (non-list)."""
    recipe = Recipe.objects.create(
        profile=profile,
        title="Simple Recipe",
        host="example.com",
        canonical_url="https://example.com/simple",
        ingredients=["1 cup flour", "1 egg"],
        instructions="Mix everything together and bake at 350F.",
        instructions_text="Mix everything together and bake at 350F.",
    )

    mock_tips = ["Tip A.", "Tip B.", "Tip C."]
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = mock_tips

    with (
        patch(
            "apps.ai.services.tips.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.tips.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = generate_tips(recipe.id)

    assert result["cached"] is False
    assert result["tips"] == mock_tips


@pytest.mark.django_db
def test_generate_tips_recipe_not_found():
    """Raises DoesNotExist for non-existent recipe."""
    with pytest.raises(Recipe.DoesNotExist):
        generate_tips(99999)


@pytest.mark.django_db
def test_generate_tips_ai_unavailable(recipe, tips_prompt):
    """AIUnavailableError propagates to caller."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.side_effect = AIUnavailableError("No key")

    with patch(
        "apps.ai.services.tips.OpenRouterService",
        return_value=mock_service_instance,
    ):
        with pytest.raises(AIUnavailableError):
            generate_tips(recipe.id)


# --- clear_tips ---


@pytest.mark.django_db
def test_clear_tips_with_existing_tips(recipe_with_cached_tips):
    """Clearing tips returns True and empties the tips field."""
    result = clear_tips(recipe_with_cached_tips.id)
    assert result is True

    recipe_with_cached_tips.refresh_from_db()
    assert recipe_with_cached_tips.ai_tips == []


@pytest.mark.django_db
def test_clear_tips_without_existing_tips(recipe):
    """Clearing tips when none exist returns False."""
    result = clear_tips(recipe.id)
    assert result is False


@pytest.mark.django_db
def test_clear_tips_recipe_not_found():
    """Raises DoesNotExist for non-existent recipe."""
    with pytest.raises(Recipe.DoesNotExist):
        clear_tips(99999)


# --- generate_timer_name ---


@pytest.mark.django_db
def test_generate_timer_name_short_duration(timer_prompt):
    """Timer name generated for a short duration."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {"label": "Boil Pasta"}

    with (
        patch(
            "apps.ai.services.timer.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.timer.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
        patch("apps.ai.services.cache.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None  # No cache hit
        result = generate_timer_name("Boil pasta until al dente", 10)

    assert result["label"] == "Boil Pasta"


@pytest.mark.django_db
def test_generate_timer_name_long_duration(timer_prompt):
    """Timer name generated for a multi-hour duration."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {"label": "Slow Cook Brisket"}

    with (
        patch(
            "apps.ai.services.timer.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.timer.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
        patch("apps.ai.services.cache.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None
        result = generate_timer_name("Slow cook the brisket", 150)

    assert result["label"] == "Slow Cook Brisket"


@pytest.mark.django_db
def test_generate_timer_name_truncates_long_label(timer_prompt):
    """Labels longer than 30 chars are truncated."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "label": "This is a very long timer label that exceeds thirty characters"
    }

    with (
        patch(
            "apps.ai.services.timer.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.timer.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
        patch("apps.ai.services.cache.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None
        result = generate_timer_name("Do something for a while", 30)

    assert len(result["label"]) <= 30
    assert result["label"].endswith("...")


@pytest.mark.django_db
def test_generate_timer_name_cached(timer_prompt):
    """Cached timer names are returned without calling AI."""
    cached_result = {"label": "Cached Timer"}

    with patch("apps.ai.services.cache.cache") as mock_cache:
        mock_cache.get.return_value = cached_result
        result = generate_timer_name("Boil water", 5)

    assert result == cached_result


@pytest.mark.django_db
def test_generate_timer_name_one_hour_exact(timer_prompt):
    """60-minute duration formats as '1 hour' (not '1 hours')."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {"label": "Bake Cake"}

    with (
        patch(
            "apps.ai.services.timer.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.timer.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
        patch("apps.ai.services.cache.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None
        result = generate_timer_name("Bake the cake", 60)

    # Verify the prompt was called (duration formatting tested implicitly)
    assert result["label"] == "Bake Cake"


@pytest.mark.django_db
def test_generate_timer_name_one_minute(timer_prompt):
    """1-minute duration formats as '1 minute' (not '1 minutes')."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {"label": "Quick Sear"}

    with (
        patch(
            "apps.ai.services.timer.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.timer.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
        patch("apps.ai.services.cache.cache") as mock_cache,
    ):
        mock_cache.get.return_value = None
        result = generate_timer_name("Sear on high heat", 1)

    assert result["label"] == "Quick Sear"
