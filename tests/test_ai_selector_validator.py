"""
Tests for the AI selector repair and response validator services (T049).

Tests:
- apps/ai/services/selector.py: repair_selector(), get_sources_needing_attention()
- apps/ai/services/validator.py: AIResponseValidator, ValidationError
"""

from unittest.mock import patch, MagicMock

import pytest

from apps.ai.models import AIPrompt
from apps.ai.services.selector import (
    repair_selector,
    get_sources_needing_attention,
    DEFAULT_CONFIDENCE_THRESHOLD,
)
from apps.ai.services.openrouter import AIUnavailableError
from apps.ai.services.validator import AIResponseValidator, ValidationError, RESPONSE_SCHEMAS
from apps.recipes.models import SearchSource


@pytest.fixture
def selector_prompt(db):
    """Get or create the selector_repair AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="selector_repair",
        defaults={
            "name": "Selector Repair",
            "system_prompt": "You are a CSS selector repair assistant.",
            "user_prompt_template": ("Fix this selector: {selector}\nTarget: {target}\nHTML:\n{html_sample}"),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def search_source(db):
    """Create a SearchSource that needs attention."""
    return SearchSource.objects.create(
        host="example.com",
        name="Example Recipes",
        is_enabled=True,
        search_url_template="https://example.com/search?q={query}",
        result_selector=".old-selector .recipe-card a",
        needs_attention=True,
    )


@pytest.fixture
def html_sample():
    """Sample HTML for selector repair tests."""
    return """
    <div class="search-results">
        <div class="recipe-item">
            <a href="/recipe/1">Chicken Curry</a>
        </div>
        <div class="recipe-item">
            <a href="/recipe/2">Beef Stew</a>
        </div>
    </div>
    """


# --- repair_selector: high confidence ---


@pytest.mark.django_db
def test_repair_selector_high_confidence_auto_updates(selector_prompt, search_source, html_sample):
    """High-confidence repair auto-updates the source selector."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "suggestions": [".recipe-item a", ".search-results a"],
        "confidence": 0.95,
    }

    with (
        patch(
            "apps.ai.services.selector.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.selector.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = repair_selector(search_source, html_sample)

    assert result["updated"] is True
    assert result["new_selector"] == ".recipe-item a"
    assert result["confidence"] == 0.95
    assert result["original_selector"] == ".old-selector .recipe-card a"

    # Verify source was updated in DB
    search_source.refresh_from_db()
    assert search_source.result_selector == ".recipe-item a"
    assert search_source.needs_attention is False


# --- repair_selector: low confidence ---


@pytest.mark.django_db
def test_repair_selector_low_confidence_no_update(selector_prompt, search_source, html_sample):
    """Low-confidence repair does NOT auto-update the source."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "suggestions": [".maybe-this a"],
        "confidence": 0.5,
    }

    with (
        patch(
            "apps.ai.services.selector.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.selector.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = repair_selector(search_source, html_sample)

    assert result["updated"] is False
    assert result["new_selector"] is None
    assert result["suggestions"] == [".maybe-this a"]

    # Source should NOT be changed
    search_source.refresh_from_db()
    assert search_source.result_selector == ".old-selector .recipe-card a"
    assert search_source.needs_attention is True


# --- repair_selector: auto_update=False ---


@pytest.mark.django_db
def test_repair_selector_auto_update_disabled(selector_prompt, search_source, html_sample):
    """Even high confidence doesn't update when auto_update=False."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "suggestions": [".recipe-item a"],
        "confidence": 0.99,
    }

    with (
        patch(
            "apps.ai.services.selector.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.selector.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = repair_selector(search_source, html_sample, auto_update=False)

    assert result["updated"] is False
    assert result["new_selector"] is None


# --- repair_selector: no suggestions ---


@pytest.mark.django_db
def test_repair_selector_empty_suggestions(selector_prompt, search_source, html_sample):
    """No suggestions means no update, even with high confidence."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "suggestions": [],
        "confidence": 0.9,
    }

    with (
        patch(
            "apps.ai.services.selector.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.selector.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = repair_selector(search_source, html_sample)

    assert result["updated"] is False


# --- repair_selector: custom confidence threshold ---


@pytest.mark.django_db
def test_repair_selector_custom_threshold(selector_prompt, search_source, html_sample):
    """Custom confidence threshold is respected."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = {
        "suggestions": [".recipe-item a"],
        "confidence": 0.85,
    }

    with (
        patch(
            "apps.ai.services.selector.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.selector.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        # With threshold=0.9, confidence 0.85 should NOT trigger update
        result = repair_selector(search_source, html_sample, confidence_threshold=0.9)

    assert result["updated"] is False


# --- get_sources_needing_attention ---


@pytest.mark.django_db
def test_get_sources_needing_attention(search_source):
    """Returns enabled sources with needs_attention=True."""
    sources = get_sources_needing_attention()
    assert len(sources) == 1
    assert sources[0].host == "example.com"


@pytest.mark.django_db
def test_get_sources_needing_attention_excludes_disabled(db):
    """Disabled sources are not returned."""
    SearchSource.objects.create(
        host="disabled.com",
        name="Disabled Source",
        is_enabled=False,
        search_url_template="https://disabled.com/search?q={query}",
        result_selector=".old",
        needs_attention=True,
    )
    sources = get_sources_needing_attention()
    assert len(sources) == 0


@pytest.mark.django_db
def test_get_sources_needing_attention_excludes_healthy(db):
    """Sources not needing attention are not returned."""
    SearchSource.objects.create(
        host="healthy.com",
        name="Healthy Source",
        is_enabled=True,
        search_url_template="https://healthy.com/search?q={query}",
        result_selector=".good",
        needs_attention=False,
    )
    sources = get_sources_needing_attention()
    assert len(sources) == 0


# --- DEFAULT_CONFIDENCE_THRESHOLD ---


def test_default_confidence_threshold():
    """Default threshold is 0.8."""
    assert DEFAULT_CONFIDENCE_THRESHOLD == 0.8


# --- AIResponseValidator ---


class TestAIResponseValidator:
    """Tests for the AIResponseValidator class."""

    def setup_method(self):
        self.validator = AIResponseValidator()

    def test_validate_search_ranking_valid(self):
        """Valid search ranking response passes."""
        result = self.validator.validate("search_ranking", [2, 0, 1, 3])
        assert result == [2, 0, 1, 3]

    def test_validate_search_ranking_empty(self):
        """Empty array is valid for search ranking."""
        result = self.validator.validate("search_ranking", [])
        assert result == []

    def test_validate_search_ranking_invalid_type(self):
        """Non-array fails search ranking validation."""
        with pytest.raises(ValidationError):
            self.validator.validate("search_ranking", {"indices": [0, 1]})

    def test_validate_tips_generation_valid(self):
        """Valid tips response (3-5 strings) passes."""
        tips = ["Tip 1", "Tip 2", "Tip 3"]
        result = self.validator.validate("tips_generation", tips)
        assert result == tips

    def test_validate_tips_generation_too_few(self):
        """Fewer than 3 tips fails validation."""
        with pytest.raises(ValidationError):
            self.validator.validate("tips_generation", ["Tip 1", "Tip 2"])

    def test_validate_tips_generation_too_many(self):
        """More than 5 tips fails validation."""
        with pytest.raises(ValidationError):
            self.validator.validate(
                "tips_generation",
                ["T1", "T2", "T3", "T4", "T5", "T6"],
            )

    def test_validate_timer_naming_valid(self):
        """Valid timer naming response passes."""
        result = self.validator.validate("timer_naming", {"label": "Boil Water"})
        assert result == {"label": "Boil Water"}

    def test_validate_timer_naming_missing_label(self):
        """Missing label field fails validation."""
        with pytest.raises(ValidationError):
            self.validator.validate("timer_naming", {"name": "Boil Water"})

    def test_validate_selector_repair_valid(self):
        """Valid selector repair response passes."""
        response = {
            "suggestions": [".new-selector a"],
            "confidence": 0.85,
        }
        result = self.validator.validate("selector_repair", response)
        assert result == response

    def test_validate_selector_repair_missing_confidence(self):
        """Missing confidence field fails validation."""
        with pytest.raises(ValidationError):
            self.validator.validate(
                "selector_repair",
                {"suggestions": [".a"]},
            )

    def test_validate_unknown_prompt_type(self):
        """Unknown prompt type raises ValidationError."""
        with pytest.raises(ValidationError, match="Unknown prompt type"):
            self.validator.validate("nonexistent_type", {})

    def test_get_schema_returns_schema(self):
        """get_schema returns schema for known type."""
        schema = self.validator.get_schema("timer_naming")
        assert schema is not None
        assert schema["type"] == "object"
        assert "label" in schema["properties"]

    def test_get_schema_returns_none_for_unknown(self):
        """get_schema returns None for unknown type."""
        assert self.validator.get_schema("nonexistent") is None

    def test_validation_error_has_errors_list(self):
        """ValidationError includes detailed error messages."""
        with pytest.raises(ValidationError) as exc_info:
            self.validator.validate("timer_naming", {"wrong": "field"})
        assert len(exc_info.value.errors) > 0

    def test_validate_recipe_remix_valid(self):
        """Valid recipe remix response passes."""
        response = {
            "title": "Vegan Cake",
            "description": "A plant-based cake",
            "ingredients": ["flour", "sugar"],
            "instructions": ["Mix", "Bake"],
        }
        result = self.validator.validate("recipe_remix", response)
        assert result["title"] == "Vegan Cake"

    def test_validate_serving_adjustment_valid(self):
        """Valid serving adjustment response passes."""
        response = {"ingredients": ["2 cups flour", "3 eggs"]}
        result = self.validator.validate("serving_adjustment", response)
        assert len(result["ingredients"]) == 2

    def test_response_schemas_has_all_types(self):
        """All expected prompt types have schemas defined."""
        expected = [
            "recipe_remix",
            "serving_adjustment",
            "tips_generation",
            "timer_naming",
            "remix_suggestions",
            "discover_favorites",
            "discover_seasonal",
            "discover_new",
            "search_ranking",
            "selector_repair",
            "nutrition_estimate",
        ]
        for prompt_type in expected:
            assert prompt_type in RESPONSE_SCHEMAS, f"Missing schema for {prompt_type}"
