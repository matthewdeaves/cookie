"""
Tests for the AI discover suggestions service (T033).

Tests the discover service at apps/ai/services/discover.py:
- Generating suggestions for profiles with/without history
- Caching behavior (24-hour TTL)
- API endpoint returning 404 for non-existent profiles
- Mocked OpenRouter API calls
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

import pytest
from django.test import Client
from django.utils import timezone

from apps.ai.models import AIDiscoverySuggestion, AIPrompt
from apps.ai.services.discover import (
    get_discover_suggestions,
    _get_season,
    CACHE_DURATION_HOURS,
)
from apps.profiles.models import Profile
from apps.recipes.models import Recipe, RecipeViewHistory


@pytest.fixture
def client():
    return Client(enforce_csrf_checks=False)


@pytest.fixture
def profile(db):
    """Create a test profile."""
    return Profile.objects.create(name="Test User", avatar_color="#d97850")


@pytest.fixture
def seasonal_prompt(db):
    """Get or create the discover_seasonal AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="discover_seasonal",
        defaults={
            "name": "Discover Seasonal",
            "system_prompt": "You are a helpful cooking assistant.",
            "user_prompt_template": "Suggest seasonal recipes for {date} ({season}).",
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def favorites_prompt(db):
    """Get or create the discover_favorites AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="discover_favorites",
        defaults={
            "name": "Discover from Favorites",
            "system_prompt": "You are a helpful cooking assistant.",
            "user_prompt_template": "Based on these favorites:\n{favorites}\nSuggest similar recipes.",
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def new_prompt(db):
    """Get or create the discover_new AI prompt."""
    prompt, _ = AIPrompt.objects.get_or_create(
        prompt_type="discover_new",
        defaults={
            "name": "Discover New",
            "system_prompt": "You are a helpful cooking assistant.",
            "user_prompt_template": "Based on this history:\n{history}\nSuggest something new.",
            "model": "anthropic/claude-3.5-haiku",
            "is_active": True,
        },
    )
    return prompt


@pytest.fixture
def all_prompts(seasonal_prompt, favorites_prompt, new_prompt):
    """Ensure all discover-related prompts exist."""
    return {
        "seasonal": seasonal_prompt,
        "favorites": favorites_prompt,
        "new": new_prompt,
    }


@pytest.fixture
def recipe_with_history(profile, db):
    """Create a recipe and view history for the profile."""
    recipe = Recipe.objects.create(
        profile=profile,
        title="Chicken Tikka Masala",
        host="example.com",
        canonical_url="https://example.com/chicken-tikka",
        cuisine="Indian",
        category="Dinner",
    )
    RecipeViewHistory.objects.create(profile=profile, recipe=recipe)
    return recipe


def _mock_ai_suggestions(suggestion_type):
    """Return mock AI validated suggestions for a given type."""
    return [
        {
            "title": f"Test {suggestion_type.title()} Suggestion 1",
            "description": f"A great {suggestion_type} recipe idea.",
            "search_query": f"{suggestion_type} recipe 1",
        },
        {
            "title": f"Test {suggestion_type.title()} Suggestion 2",
            "description": f"Another {suggestion_type} recipe idea.",
            "search_query": f"{suggestion_type} recipe 2",
        },
    ]


# --- _get_season helper ---


def test_get_season_winter():
    """December, January, February are winter."""
    from datetime import datetime

    assert _get_season(datetime(2024, 12, 1)) == "winter"
    assert _get_season(datetime(2024, 1, 15)) == "winter"
    assert _get_season(datetime(2024, 2, 28)) == "winter"


def test_get_season_spring():
    """March, April, May are spring."""
    from datetime import datetime

    assert _get_season(datetime(2024, 3, 1)) == "spring"
    assert _get_season(datetime(2024, 4, 15)) == "spring"
    assert _get_season(datetime(2024, 5, 31)) == "spring"


def test_get_season_summer():
    """June, July, August are summer."""
    from datetime import datetime

    assert _get_season(datetime(2024, 6, 1)) == "summer"
    assert _get_season(datetime(2024, 7, 4)) == "summer"
    assert _get_season(datetime(2024, 8, 31)) == "summer"


def test_get_season_autumn():
    """September, October, November are autumn."""
    from datetime import datetime

    assert _get_season(datetime(2024, 9, 1)) == "autumn"
    assert _get_season(datetime(2024, 10, 31)) == "autumn"
    assert _get_season(datetime(2024, 11, 30)) == "autumn"


# --- Cached suggestions ---


@pytest.mark.django_db
def test_returns_cached_suggestions(profile, seasonal_prompt):
    """Cached suggestions (within 24h) are returned without calling AI."""
    # Pre-populate cache
    AIDiscoverySuggestion.objects.create(
        profile=profile,
        suggestion_type="seasonal",
        title="Cached Suggestion",
        description="From cache",
        search_query="cached recipe",
    )

    with patch("apps.ai.services.discover.OpenRouterService") as mock_service:
        result = get_discover_suggestions(profile.id)

    # AI should NOT have been called
    mock_service.assert_not_called()

    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["title"] == "Cached Suggestion"
    assert result["suggestions"][0]["type"] == "seasonal"
    assert "refreshed_at" in result


@pytest.mark.django_db
def test_expired_cache_triggers_new_generation(profile, seasonal_prompt):
    """Suggestions older than 24h are expired and regenerated."""
    # Create an old cached suggestion
    old_suggestion = AIDiscoverySuggestion.objects.create(
        profile=profile,
        suggestion_type="seasonal",
        title="Old Suggestion",
        description="Expired",
        search_query="old recipe",
    )
    # Manually set created_at to >24h ago
    expired_time = timezone.now() - timedelta(hours=CACHE_DURATION_HOURS + 1)
    AIDiscoverySuggestion.objects.filter(id=old_suggestion.id).update(created_at=expired_time)

    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked response"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = _mock_ai_suggestions("seasonal")

    with (
        patch("apps.ai.services.discover.OpenRouterService", return_value=mock_service_instance),
        patch("apps.ai.services.discover.AIResponseValidator", return_value=mock_validator_instance),
    ):
        result = get_discover_suggestions(profile.id)

    # Old suggestion should be deleted
    assert not AIDiscoverySuggestion.objects.filter(id=old_suggestion.id).exists()

    # New suggestions should have been created
    assert len(result["suggestions"]) == 2
    assert result["suggestions"][0]["title"] == "Test Seasonal Suggestion 1"


# --- New user (no history) ---


@pytest.mark.django_db
def test_new_user_gets_only_seasonal(profile, seasonal_prompt):
    """User with no view history gets only seasonal suggestions."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = _mock_ai_suggestions("seasonal")

    with (
        patch("apps.ai.services.discover.OpenRouterService", return_value=mock_service_instance),
        patch("apps.ai.services.discover.AIResponseValidator", return_value=mock_validator_instance),
    ):
        result = get_discover_suggestions(profile.id)

    assert len(result["suggestions"]) == 2
    for s in result["suggestions"]:
        assert s["type"] == "seasonal"


# --- User with history ---


@pytest.mark.django_db(transaction=True)
def test_user_with_history_gets_all_types(profile, all_prompts, recipe_with_history):
    """User with view history gets seasonal, favorites, and new suggestions."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    # Map prompt_type to suggestion type — thread-safe since each thread calls with a different prompt_type
    prompt_to_type = {
        "discover_seasonal": "seasonal",
        "discover_favorites": "favorites",
        "discover_new": "new",
    }

    def mock_validate(prompt_type, response):
        stype = prompt_to_type.get(prompt_type, "seasonal")
        return _mock_ai_suggestions(stype)

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.side_effect = mock_validate

    with (
        patch("apps.ai.services.discover.OpenRouterService", return_value=mock_service_instance),
        patch("apps.ai.services.discover.AIResponseValidator", return_value=mock_validator_instance),
    ):
        result = get_discover_suggestions(profile.id)

    # Should have 6 total suggestions: 2 seasonal + 2 favorites + 2 new
    assert len(result["suggestions"]) == 6
    types = [s["type"] for s in result["suggestions"]]
    assert types.count("seasonal") == 2
    assert types.count("favorites") == 2
    assert types.count("new") == 2


# --- Profile not found ---


@pytest.mark.django_db
def test_discover_nonexistent_profile_raises():
    """get_discover_suggestions raises Profile.DoesNotExist for bad profile_id."""
    with pytest.raises(Profile.DoesNotExist):
        get_discover_suggestions(99999)


# --- API Endpoint ---


@pytest.mark.django_db
def test_discover_endpoint_not_found(client):
    """GET /api/ai/discover/99999/ returns 404."""
    response = client.get("/api/ai/discover/99999/")
    assert response.status_code == 404
    data = json.loads(response.content)
    assert data["error"] == "not_found"


@pytest.mark.django_db
def test_discover_endpoint_returns_cached(client, profile):
    """GET /api/ai/discover/{id}/ returns cached suggestions."""
    AIDiscoverySuggestion.objects.create(
        profile=profile,
        suggestion_type="seasonal",
        title="Spring Salads",
        description="Fresh spring salad ideas",
        search_query="spring salad recipes",
    )

    response = client.get(f"/api/ai/discover/{profile.id}/")
    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["title"] == "Spring Salads"
    assert data["suggestions"][0]["search_query"] == "spring salad recipes"
    assert "refreshed_at" in data


@pytest.mark.django_db
def test_discover_endpoint_with_mocked_ai(client, profile, seasonal_prompt):
    """GET /api/ai/discover/{id}/ generates suggestions via mocked AI."""
    mock_service_instance = MagicMock()
    mock_service_instance.complete.return_value = "mocked"

    mock_validator_instance = MagicMock()
    mock_validator_instance.validate.return_value = [
        {
            "title": "Summer BBQ",
            "description": "Great grilling recipes",
            "search_query": "summer bbq recipes",
        },
    ]

    with (
        patch("apps.ai.services.discover.OpenRouterService", return_value=mock_service_instance),
        patch("apps.ai.services.discover.AIResponseValidator", return_value=mock_validator_instance),
    ):
        response = client.get(f"/api/ai/discover/{profile.id}/")

    assert response.status_code == 200
    data = json.loads(response.content)
    assert len(data["suggestions"]) == 1
    assert data["suggestions"][0]["title"] == "Summer BBQ"


# --- AI failure graceful handling ---


@pytest.mark.django_db
def test_ai_failure_returns_empty_suggestions(profile, seasonal_prompt):
    """When AI service fails, seasonal generation returns empty list."""
    from apps.ai.services.openrouter import AIUnavailableError

    mock_service_instance = MagicMock()
    mock_service_instance.complete.side_effect = AIUnavailableError("No API key")

    with patch("apps.ai.services.discover.OpenRouterService", return_value=mock_service_instance):
        result = get_discover_suggestions(profile.id)

    assert result["suggestions"] == []


# --- Missing prompt handling ---


@pytest.mark.django_db
def test_missing_prompt_returns_empty(profile):
    """When discover_seasonal prompt is missing, returns empty suggestions."""
    # No prompts created at all
    result = get_discover_suggestions(profile.id)
    assert result["suggestions"] == []


# --- Cache duration constant ---


def test_cache_duration_is_24_hours():
    """Verify cache duration constant is 24 hours."""
    assert CACHE_DURATION_HOURS == 24


# --- Format suggestions ---


@pytest.mark.django_db
def test_format_suggestions_from_queryset(profile):
    """_format_suggestions works with QuerySet input."""
    from apps.ai.services.discover import _format_suggestions

    AIDiscoverySuggestion.objects.create(
        profile=profile,
        suggestion_type="seasonal",
        title="Test",
        description="Desc",
        search_query="query",
    )
    qs = AIDiscoverySuggestion.objects.filter(profile=profile)
    result = _format_suggestions(qs)
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["type"] == "seasonal"
    assert result["suggestions"][0]["title"] == "Test"
    assert "refreshed_at" in result


@pytest.mark.django_db
def test_format_suggestions_from_list(profile):
    """_format_suggestions works with list input."""
    from apps.ai.services.discover import _format_suggestions

    suggestion = AIDiscoverySuggestion.objects.create(
        profile=profile,
        suggestion_type="new",
        title="New Thing",
        description="Try this",
        search_query="new recipe",
    )
    result = _format_suggestions([suggestion])
    assert len(result["suggestions"]) == 1
    assert result["suggestions"][0]["type"] == "new"
    assert result["suggestions"][0]["title"] == "New Thing"
