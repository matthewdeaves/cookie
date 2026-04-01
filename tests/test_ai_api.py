"""
Tests for AI API endpoints (apps/ai/api.py).

Covers all 11 endpoints at the API layer: auth, rate limits,
error handling decorator, schemas, and quota enforcement.
Services behind endpoints are mocked — no real OpenRouter calls.
"""

import json
from unittest.mock import patch, MagicMock

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.ai.services.openrouter import AIUnavailableError, AIResponseError
from apps.core.models import AppSettings
from apps.profiles.models import Profile
from apps.recipes.models import Recipe, SearchSource


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def profile(db):
    return Profile.objects.create(name="Test User", avatar_color="#d97850")


@pytest.fixture
def auth_client(client, profile):
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


@pytest.fixture
def recipe(profile):
    return Recipe.objects.create(
        profile=profile,
        title="Spaghetti Carbonara",
        host="example.com",
        canonical_url="https://example.com/carbonara",
        ingredients=["400g spaghetti", "200g pancetta"],
        instructions=[{"text": "Cook pasta"}, {"text": "Fry pancetta"}],
    )


@pytest.fixture
def search_source(db):
    return SearchSource.objects.create(
        host="example.com",
        name="Example",
        search_url_template="https://example.com/search?q={query}",
        result_selector=".recipe-card",
        consecutive_failures=5,
        needs_attention=True,
    )


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


def _create_user(username, is_staff=False):
    user = User.objects.create_user(
        username=username,
        password="!",
        email="",
        is_active=True,
        is_staff=is_staff,
    )
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login(client, user):
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()


# ── GET /api/ai/status ──


@pytest.mark.django_db
class TestAIStatus:
    def test_no_key_configured(self, client):
        response = client.get("/api/ai/status")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["configured"] is False
        assert data["error_code"] == "no_api_key"

    @patch.object(AppSettings, "get")
    @patch("apps.ai.api.OpenRouterService.validate_key_cached", return_value=(False, "Invalid key"))
    def test_key_invalid(self, mock_validate, mock_get, client):
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "sk-bad"  # pragma: allowlist secret
        mock_settings.default_ai_model = "anthropic/claude-haiku-4.5"
        mock_get.return_value = mock_settings

        response = client.get("/api/ai/status")
        data = response.json()
        assert data["available"] is False
        assert data["configured"] is True
        assert data["valid"] is False
        assert data["error_code"] == "invalid_api_key"

    @patch.object(AppSettings, "get")
    @patch("apps.ai.api.OpenRouterService.validate_key_cached", return_value=(True, None))
    def test_key_valid(self, mock_validate, mock_get, client):
        mock_settings = MagicMock()
        mock_settings.openrouter_api_key = "sk-good"  # pragma: allowlist secret
        mock_settings.default_ai_model = "anthropic/claude-haiku-4.5"
        mock_get.return_value = mock_settings

        response = client.get("/api/ai/status")
        data = response.json()
        assert data["available"] is True
        assert data["configured"] is True
        assert data["valid"] is True
        assert data["error"] is None


# ── POST /api/ai/test-api-key ──


@pytest.mark.django_db
class TestTestApiKey:
    def test_requires_admin_in_passkey_mode(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)
        response = client.post(
            "/api/ai/test-api-key",
            data=json.dumps({"api_key": "sk-test"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("apps.ai.api.OpenRouterService.test_connection", return_value=(True, "Valid key"))
    def test_valid_key(self, mock_conn, auth_client):
        response = auth_client.post(
            "/api/ai/test-api-key",
            data=json.dumps({"api_key": "sk-good"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @patch("apps.ai.api.OpenRouterService.test_connection", return_value=(False, "Bad key"))
    def test_invalid_key(self, mock_conn, auth_client):
        response = auth_client.post(
            "/api/ai/test-api-key",
            data=json.dumps({"api_key": "sk-bad"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert data["message"] == "Bad key"

    def test_empty_key_returns_400(self, auth_client):
        response = auth_client.post(
            "/api/ai/test-api-key",
            data=json.dumps({"api_key": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400


# ── POST /api/ai/save-api-key ──


@pytest.mark.django_db
class TestSaveApiKey:
    def test_requires_admin_in_passkey_mode(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)
        response = client.post(
            "/api/ai/save-api-key",
            data=json.dumps({"api_key": "sk-test"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("apps.ai.api.OpenRouterService.invalidate_key_cache")
    def test_saves_key(self, mock_invalidate, auth_client):
        response = auth_client.post(
            "/api/ai/save-api-key",
            data=json.dumps({"api_key": "sk-new-key"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        settings = AppSettings.get()
        assert settings.openrouter_api_key == "sk-new-key"  # pragma: allowlist secret
        mock_invalidate.assert_called_once()


# ── GET /api/ai/prompts ──


@pytest.mark.django_db
class TestPrompts:
    def test_list_prompts(self, client):
        """Seeded prompts are returned."""
        response = client.get("/api/ai/prompts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        types = {p["prompt_type"] for p in data}
        assert "tips_generation" in types

    def test_get_prompt(self, client):
        """Get a seeded prompt by type."""
        response = client.get("/api/ai/prompts/tips_generation")
        assert response.status_code == 200
        data = response.json()
        assert data["prompt_type"] == "tips_generation"
        assert data["is_active"] is True

    def test_get_prompt_not_found(self, client):
        response = client.get("/api/ai/prompts/nonexistent")
        assert response.status_code == 404

    def test_update_prompt(self, auth_client):
        response = auth_client.put(
            "/api/ai/prompts/tips_generation",
            data=json.dumps({"system_prompt": "You are a pastry chef.", "is_active": False}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["system_prompt"] == "You are a pastry chef."
        assert data["is_active"] is False

    def test_update_prompt_not_found(self, auth_client):
        response = auth_client.put(
            "/api/ai/prompts/nonexistent",
            data=json.dumps({"system_prompt": "new"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    @patch("apps.ai.api.OpenRouterService")
    def test_update_prompt_invalid_model(self, mock_service_cls, auth_client):
        mock_instance = MagicMock()
        mock_instance.get_available_models.return_value = [{"id": "anthropic/claude-haiku-4.5"}]
        mock_service_cls.return_value = mock_instance

        response = auth_client.put(
            "/api/ai/prompts/tips_generation",
            data=json.dumps({"model": "nonexistent/model"}),
            content_type="application/json",
        )
        assert response.status_code == 422
        assert response.json()["error"] == "invalid_model"

    def test_update_requires_admin_in_passkey_mode(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)
        response = client.put(
            "/api/ai/prompts/tips_generation",
            data=json.dumps({"is_active": False}),
            content_type="application/json",
        )
        assert response.status_code == 401


# ── GET /api/ai/models ──


@pytest.mark.django_db
class TestModels:
    @patch("apps.ai.api.OpenRouterService")
    def test_returns_models(self, mock_cls, client):
        mock_instance = MagicMock()
        mock_instance.get_available_models.return_value = [
            {"id": "anthropic/claude-haiku-4.5", "name": "Claude Haiku"},
        ]
        mock_cls.return_value = mock_instance

        response = client.get("/api/ai/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "anthropic/claude-haiku-4.5"

    @patch("apps.ai.api.OpenRouterService", side_effect=AIUnavailableError("No key"))
    def test_no_key_returns_empty(self, mock_cls, client):
        response = client.get("/api/ai/models")
        assert response.status_code == 200
        assert response.json() == []

    @patch("apps.ai.api.OpenRouterService")
    def test_api_error_returns_empty(self, mock_cls, client):
        mock_instance = MagicMock()
        mock_instance.get_available_models.side_effect = AIResponseError("API error")
        mock_cls.return_value = mock_instance

        response = client.get("/api/ai/models")
        assert response.status_code == 200
        assert response.json() == []


# ── POST /api/ai/tips ──


@pytest.mark.django_db
class TestTipsEndpoint:
    def test_requires_auth(self, client):
        response = client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.generate_tips", return_value={"tips": ["Tip 1", "Tip 2"], "cached": False})
    def test_success(self, mock_tips, mock_quota, auth_client, recipe):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tips"] == ["Tip 1", "Tip 2"]
        assert data["cached"] is False

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    def test_recipe_not_found(self, mock_release, mock_quota, auth_client):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": 99999}),
            content_type="application/json",
        )
        assert response.status_code == 404
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    def test_recipe_not_owned(self, mock_release, mock_quota, auth_client):
        other_profile = Profile.objects.create(name="Other", avatar_color="#000000")
        other_recipe = Recipe.objects.create(
            profile=other_profile,
            title="Other Recipe",
            host="example.com",
            ingredients=["flour"],
            instructions=[{"text": "mix"}],
        )
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": other_recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 404
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(False, {"remaining": 0, "limit": 10}))
    def test_quota_exceeded(self, mock_quota, auth_client, recipe):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 429
        assert response.json()["error"] == "quota_exceeded"

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    @patch("apps.ai.api.generate_tips", side_effect=AIUnavailableError("No key"))
    def test_ai_unavailable(self, mock_tips, mock_release, mock_quota, auth_client, recipe):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 503
        assert response.json()["error"] == "ai_unavailable"
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    @patch("apps.ai.api.generate_tips", side_effect=AIResponseError("Bad response"))
    def test_ai_response_error(self, mock_tips, mock_release, mock_quota, auth_client, recipe):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["error"] == "ai_error"
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    @patch("apps.ai.api.generate_tips", return_value={"tips": ["Cached tip"], "cached": True})
    @patch("apps.ai.api.is_ai_cache_hit", return_value=False)
    def test_cached_result_releases_quota(self, mock_cache, mock_tips, mock_release, mock_quota, auth_client, recipe):
        response = auth_client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": recipe.id}),
            content_type="application/json",
        )
        assert response.status_code == 200
        mock_release.assert_called_once()


# ── POST /api/ai/timer-name ──


@pytest.mark.django_db
class TestTimerNameEndpoint:
    def test_requires_auth(self, client):
        response = client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil pasta", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("apps.ai.api.is_ai_cache_hit", return_value=False)
    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.generate_timer_name", return_value={"label": "Boil Pasta"})
    def test_success(self, mock_timer, mock_quota, mock_cache, auth_client):
        response = auth_client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil pasta", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["label"] == "Boil Pasta"

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    def test_empty_step_text(self, mock_release, mock_quota, auth_client):
        response = auth_client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["error"] == "validation_error"
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    def test_negative_duration(self, mock_release, mock_quota, auth_client):
        response = auth_client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil", "duration_minutes": -1}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["error"] == "validation_error"
        mock_release.assert_called_once()

    @patch("apps.ai.api.reserve_quota", return_value=(False, {"remaining": 0, "limit": 20}))
    def test_quota_exceeded(self, mock_quota, auth_client):
        response = auth_client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 429
        assert response.json()["error"] == "quota_exceeded"

    @patch("apps.ai.api.is_ai_cache_hit", return_value=False)
    @patch("apps.ai.api.reserve_quota", return_value=(True, {}))
    @patch("apps.ai.api.release_quota")
    @patch("apps.ai.api.generate_timer_name", side_effect=AIUnavailableError("No key"))
    def test_ai_unavailable(self, mock_timer, mock_release, mock_quota, mock_cache, auth_client):
        response = auth_client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 503
        assert response.json()["error"] == "ai_unavailable"
        mock_release.assert_called_once()


# ── POST /api/ai/repair-selector ──


@pytest.mark.django_db
class TestRepairSelectorEndpoint:
    def test_requires_admin_in_passkey_mode(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)
        response = client.post(
            "/api/ai/repair-selector",
            data=json.dumps({"source_id": 1, "html_sample": "<div>test</div>"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    @patch("apps.ai.api.repair_selector")
    def test_success(self, mock_repair, auth_client, search_source):
        mock_repair.return_value = {
            "suggestions": [".recipe-item"],
            "confidence": 0.9,
            "original_selector": ".recipe-card",
            "updated": True,
            "new_selector": ".recipe-item",
        }
        response = auth_client.post(
            "/api/ai/repair-selector",
            data=json.dumps(
                {
                    "source_id": search_source.id,
                    "html_sample": "<div class='recipe-item'>Recipe</div>",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["suggestions"] == [".recipe-item"]
        assert data["confidence"] == 0.9
        assert data["updated"] is True

    def test_source_not_found(self, auth_client):
        response = auth_client.post(
            "/api/ai/repair-selector",
            data=json.dumps({"source_id": 99999, "html_sample": "<div>test</div>"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_empty_html(self, auth_client, search_source):
        response = auth_client.post(
            "/api/ai/repair-selector",
            data=json.dumps({"source_id": search_source.id, "html_sample": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["error"] == "validation_error"


# ── GET /api/ai/sources-needing-attention ──


@pytest.mark.django_db
class TestSourcesNeedingAttention:
    def test_requires_admin_in_passkey_mode(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)
        response = client.get("/api/ai/sources-needing-attention")
        assert response.status_code == 401

    @patch("apps.ai.api.get_sources_needing_attention")
    def test_returns_sources(self, mock_get, auth_client, search_source):
        mock_get.return_value = [search_source]
        response = auth_client.get("/api/ai/sources-needing-attention")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["host"] == "example.com"
        assert data[0]["consecutive_failures"] == 5

    @patch("apps.ai.api.get_sources_needing_attention")
    def test_returns_empty_when_none(self, mock_get, auth_client):
        mock_get.return_value = []
        response = auth_client.get("/api/ai/sources-needing-attention")
        assert response.status_code == 200
        assert response.json() == []
