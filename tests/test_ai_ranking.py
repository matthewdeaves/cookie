"""
Tests for the AI search result ranking service (T047).

Tests the ranking service at apps/ai/services/ranking.py:
- rank_results() with multiple results
- Empty results
- AI failure fallback behavior (image-first sorting)
- _apply_ranking() index mapping
- _filter_valid() and _sort_by_image() helpers
"""

from unittest.mock import patch, MagicMock

import pytest

from apps.ai.models import AIPrompt
from apps.ai.services.ranking import (
    rank_results,
    is_ranking_available,
    _apply_ranking,
    _filter_valid,
    _sort_by_image,
)
from apps.ai.services.openrouter import AIUnavailableError, AIResponseError
from apps.ai.services.validator import ValidationError
from apps.core.models import AppSettings


@pytest.fixture
def ranking_prompt(db):
    """Get or create the search_ranking AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="search_ranking",
        defaults={
            "name": "Search Ranking",
            "system_prompt": "You are a search ranking assistant.",
            "user_prompt_template": ("Rank these {count} search results for the query '{query}':\n{results}"),
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def api_key(db):
    """Configure an API key so AI ranking is available."""
    settings = AppSettings.get()
    settings.openrouter_api_key = "test-key-123"  # pragma: allowlist secret
    settings.save()
    return settings


@pytest.fixture
def sample_results():
    """Sample search results for ranking tests."""
    return [
        {
            "url": "https://example.com/recipe1",
            "title": "Chicken Tikka Masala",
            "host": "example.com",
            "image_url": "https://example.com/img1.jpg",
            "description": "A classic Indian dish",
        },
        {
            "url": "https://example.com/recipe2",
            "title": "Butter Chicken",
            "host": "example.com",
            "image_url": "",
            "description": "Creamy and delicious",
        },
        {
            "url": "https://other.com/recipe3",
            "title": "Tandoori Chicken",
            "host": "other.com",
            "image_url": "https://other.com/img3.jpg",
            "description": "Smoky grilled chicken",
        },
    ]


# --- _filter_valid ---


def test_filter_valid_removes_titleless():
    """Results without titles are filtered out."""
    results = [
        {"title": "Good Recipe", "url": "https://a.com"},
        {"title": "", "url": "https://b.com"},
        {"url": "https://c.com"},
        {"title": "Another Good", "url": "https://d.com"},
    ]
    filtered = _filter_valid(results)
    assert len(filtered) == 2
    assert filtered[0]["title"] == "Good Recipe"
    assert filtered[1]["title"] == "Another Good"


def test_filter_valid_empty_list():
    """Empty input returns empty output."""
    assert _filter_valid([]) == []


# --- _sort_by_image ---


def test_sort_by_image_prioritizes_images():
    """Results with images come first."""
    results = [
        {"title": "No Image", "image_url": ""},
        {"title": "Has Image", "image_url": "https://img.jpg"},
        {"title": "Also No Image"},
    ]
    sorted_results = _sort_by_image(results)
    assert sorted_results[0]["title"] == "Has Image"


def test_sort_by_image_filters_invalid():
    """Results without titles are filtered before sorting."""
    results = [
        {"title": "", "image_url": "https://img.jpg"},
        {"title": "Valid", "image_url": ""},
    ]
    sorted_results = _sort_by_image(results)
    assert len(sorted_results) == 1
    assert sorted_results[0]["title"] == "Valid"


# --- _apply_ranking ---


def test_apply_ranking_reorders():
    """Ranking indices reorder results correctly."""
    results = [{"id": 0}, {"id": 1}, {"id": 2}]
    ranked = _apply_ranking(results, [2, 0, 1])
    assert [r["id"] for r in ranked] == [2, 0, 1]


def test_apply_ranking_handles_missing_indices():
    """Missing indices are appended at end."""
    results = [{"id": 0}, {"id": 1}, {"id": 2}]
    ranked = _apply_ranking(results, [1])
    assert ranked[0]["id"] == 1
    assert len(ranked) == 3


def test_apply_ranking_ignores_out_of_bounds():
    """Out-of-bounds indices are ignored."""
    results = [{"id": 0}, {"id": 1}]
    ranked = _apply_ranking(results, [99, 0, 1])
    assert [r["id"] for r in ranked] == [0, 1]


def test_apply_ranking_deduplicates():
    """Duplicate indices only appear once."""
    results = [{"id": 0}, {"id": 1}]
    ranked = _apply_ranking(results, [0, 0, 1])
    assert len(ranked) == 2


# --- is_ranking_available ---


@pytest.mark.django_db
def test_ranking_available_with_api_key(api_key):
    """Ranking is available when API key is configured."""
    assert is_ranking_available() is True


@pytest.mark.django_db
def test_ranking_unavailable_without_api_key(db):
    """Ranking is not available without API key."""
    settings = AppSettings.get()
    settings._openrouter_api_key = ""
    settings.save()
    assert is_ranking_available() is False


# --- rank_results ---


@pytest.mark.django_db
def test_rank_results_empty_list(api_key, ranking_prompt):
    """Empty results return empty list."""
    result = rank_results("chicken", [])
    assert result == []


@pytest.mark.django_db
def test_rank_results_single_result(api_key, ranking_prompt):
    """Single result is returned as-is (no AI call needed)."""
    results = [{"title": "Solo Recipe", "url": "https://a.com"}]
    with patch("apps.ai.services.ranking.OpenRouterService") as mock_svc:
        result = rank_results("chicken", results)
    mock_svc.assert_not_called()
    assert len(result) == 1
    assert result[0]["title"] == "Solo Recipe"


@pytest.mark.django_db
def test_rank_results_filters_titleless(api_key, ranking_prompt):
    """Results without titles are filtered, and single remaining result returned."""
    results = [
        {"title": "Good Recipe", "url": "https://a.com"},
        {"title": "", "url": "https://b.com"},
    ]
    with patch("apps.ai.services.ranking.OpenRouterService") as mock_svc:
        result = rank_results("chicken", results)
    mock_svc.assert_not_called()
    assert len(result) == 1
    assert result[0]["title"] == "Good Recipe"


@pytest.mark.django_db
def test_rank_results_with_ai(api_key, ranking_prompt, sample_results):
    """AI ranking reorders results according to AI response."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    # AI returns reversed order
    mock_validator_instance.validate.return_value = [2, 1, 0]

    with (
        patch(
            "apps.ai.services.ranking.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.ranking.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = rank_results("chicken", sample_results)

    assert len(result) == 3
    assert result[0]["title"] == "Tandoori Chicken"
    assert result[1]["title"] == "Butter Chicken"
    assert result[2]["title"] == "Chicken Tikka Masala"


@pytest.mark.django_db
def test_rank_results_no_api_key_falls_back(db, ranking_prompt, sample_results):
    """Without API key, falls back to image-first sorting."""
    settings = AppSettings.get()
    settings._openrouter_api_key = ""
    settings.save()

    result = rank_results("chicken", sample_results)
    # Results with images should come first
    assert result[0]["image_url"] != ""
    assert len(result) == 3


@pytest.mark.django_db
def test_rank_results_ai_unavailable_falls_back(api_key, ranking_prompt, sample_results):
    """AIUnavailableError falls back to image-first sorting."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.side_effect = AIUnavailableError("No key")

    with patch(
        "apps.ai.services.ranking.OpenRouterService",
        return_value=mock_service_instance,
    ):
        result = rank_results("chicken", sample_results)

    assert len(result) == 3
    # Should still have all results, just image-sorted
    titles = [r["title"] for r in result]
    assert "Chicken Tikka Masala" in titles


@pytest.mark.django_db
def test_rank_results_ai_response_error_falls_back(api_key, ranking_prompt, sample_results):
    """AIResponseError falls back to image-first sorting."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.side_effect = AIResponseError("Bad response")

    with patch(
        "apps.ai.services.ranking.OpenRouterService",
        return_value=mock_service_instance,
    ):
        result = rank_results("chicken", sample_results)

    assert len(result) == 3


@pytest.mark.django_db
def test_rank_results_validation_error_falls_back(api_key, ranking_prompt, sample_results):
    """ValidationError falls back to image-first sorting."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.side_effect = ValidationError("Bad schema")

    with (
        patch(
            "apps.ai.services.ranking.OpenRouterService",
            return_value=mock_service_instance,
        ),
        patch(
            "apps.ai.services.ranking.AIResponseValidator",
            return_value=mock_validator_instance,
        ),
    ):
        result = rank_results("chicken", sample_results)

    assert len(result) == 3


@pytest.mark.django_db
def test_rank_results_unexpected_error_falls_back(api_key, ranking_prompt, sample_results):
    """Unexpected exceptions fall back to image-first sorting."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.side_effect = RuntimeError("Unexpected")

    with patch(
        "apps.ai.services.ranking.OpenRouterService",
        return_value=mock_service_instance,
    ):
        result = rank_results("chicken", sample_results)

    assert len(result) == 3


@pytest.mark.django_db
def test_rank_results_missing_prompt_falls_back(api_key, sample_results):
    """Missing prompt falls back to image-first sorting."""
    # No ranking_prompt fixture, so prompt doesn't exist
    # But prompts may be seeded via migration; delete it explicitly
    AIPrompt.objects.filter(prompt_type="search_ranking").delete()

    result = rank_results("chicken", sample_results)
    assert len(result) == 3
