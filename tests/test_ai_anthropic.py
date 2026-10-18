"""
Tests for the Anthropic AI service (T044).

Tests apps/ai/services/anthropic_client.py:
- AnthropicService initialization
- complete() with success and failure
- _parse_json_response() with plain JSON and markdown code blocks
- test_connection() success and failure
- validate_key_cached() with cache hit and miss
- invalidate_key_cache()
- get_available_models()
- is_available()
"""

import time
from unittest.mock import patch, MagicMock

import pytest

from apps.ai.services.anthropic_client import (
    AnthropicService,
    AIUnavailableError,
    AIResponseError,
    AIServiceError,
)


# --- Initialization ---


@pytest.mark.django_db
class TestAnthropicServiceInit:
    """Tests for AnthropicService.__init__()."""

    def test_init_with_explicit_key(self):
        service = AnthropicService(api_key="sk-test-123")  # pragma: allowlist secret
        assert service.api_key == "sk-test-123"  # pragma: allowlist secret

    def test_init_without_key_raises(self):
        """Empty API key raises AIUnavailableError."""
        with pytest.raises(AIUnavailableError, match="not configured"):
            AnthropicService(api_key="")

    def test_init_none_key_fetches_from_settings(self):
        """When api_key is None, fetches from AppSettings."""
        with patch("apps.ai.services.anthropic_client.AppSettings") as mock_settings:
            mock_settings.get.return_value = MagicMock(anthropic_api_key="sk-from-db")  # pragma: allowlist secret
            service = AnthropicService(api_key=None)
            assert service.api_key == "sk-from-db"  # pragma: allowlist secret

    def test_init_none_key_no_setting_raises(self):
        """When api_key is None and no setting configured, raises."""
        with patch("apps.ai.services.anthropic_client.AppSettings") as mock_settings:
            mock_settings.get.return_value = MagicMock(anthropic_api_key="")
            with pytest.raises(AIUnavailableError):
                AnthropicService(api_key=None)


# --- _parse_json_response ---


class TestParseJsonResponse:
    """Tests for AnthropicService._parse_json_response()."""

    def setup_method(self):
        self.service = AnthropicService(api_key="sk-test")

    def test_plain_json(self):
        result = self.service._parse_json_response('{"status": "ok"}')
        assert result == {"status": "ok"}

    def test_json_in_code_block(self):
        content = '```json\n{"status": "ok"}\n```'
        result = self.service._parse_json_response(content)
        assert result == {"status": "ok"}

    def test_json_in_plain_code_block(self):
        content = '```\n{"key": "value"}\n```'
        result = self.service._parse_json_response(content)
        assert result == {"key": "value"}

    def test_invalid_json_raises(self):
        with pytest.raises(AIResponseError, match="Invalid JSON"):
            self.service._parse_json_response("not json at all")

    def test_empty_string_raises(self):
        with pytest.raises(AIResponseError):
            self.service._parse_json_response("")


# --- complete() ---


@pytest.mark.django_db
class TestComplete:
    """Tests for AnthropicService.complete()."""

    def _make_mock_response(self, content):
        """Create a mock Anthropic Messages response."""
        mock_block = MagicMock()
        mock_block.type = "text"
        mock_block.text = content
        mock_response = MagicMock()
        mock_response.content = [mock_block]
        return mock_response

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_complete_json_success(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.messages.create.return_value = self._make_mock_response('{"result": "test"}')

        service = AnthropicService(api_key="sk-test")
        result = service.complete(
            system_prompt="Be helpful",
            user_prompt="Hello",
            json_response=True,
        )
        assert result == {"result": "test"}
        kwargs = mock_client.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-haiku-5-5"
        assert kwargs["system"] == "Be helpful"
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert kwargs["max_tokens"] > 0

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_complete_text_success(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.messages.create.return_value = self._make_mock_response("Hello there!")

        service = AnthropicService(api_key="sk-test")
        result = service.complete(
            system_prompt="Be helpful",
            user_prompt="Hello",
            json_response=False,
        )
        assert result == {"content": "Hello there!"}

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_complete_no_content_raises(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_response = MagicMock()
        mock_response.content = []
        mock_client.messages.create.return_value = mock_response

        service = AnthropicService(api_key="sk-test")
        with pytest.raises(AIResponseError, match="No content"):
            service.complete(
                system_prompt="Be helpful",
                user_prompt="Hello",
            )

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_complete_no_response_raises(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.messages.create.return_value = None

        service = AnthropicService(api_key="sk-test")
        with pytest.raises(AIResponseError, match="No content"):
            service.complete(
                system_prompt="Be helpful",
                user_prompt="Hello",
            )

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_complete_api_exception_raises(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.messages.create.side_effect = RuntimeError("Connection refused")

        service = AnthropicService(api_key="sk-test")
        with pytest.raises(AIResponseError, match="Anthropic API error"):
            service.complete(
                system_prompt="Be helpful",
                user_prompt="Hello",
            )


# --- test_connection() ---


@pytest.mark.django_db
class TestTestConnection:
    """Tests for AnthropicService.test_connection()."""

    @patch.object(AnthropicService, "complete")
    def test_success(self, mock_complete):
        mock_complete.return_value = {"status": "ok"}
        success, message = AnthropicService.test_connection("sk-valid")
        assert success is True
        assert message == "Connection successful"

    @patch.object(AnthropicService, "complete")
    def test_api_error(self, mock_complete):
        mock_complete.side_effect = AIResponseError("Bad request")
        success, message = AnthropicService.test_connection("sk-bad")
        assert success is False
        assert "API error" in message

    def test_empty_key(self):
        success, message = AnthropicService.test_connection("")
        assert success is False
        assert "not provided" in message

    @patch.object(AnthropicService, "complete")
    def test_generic_exception(self, mock_complete):
        mock_complete.side_effect = RuntimeError("Network down")
        success, message = AnthropicService.test_connection("sk-test")
        assert success is False
        assert "Connection failed" in message


# --- validate_key_cached() ---


@pytest.mark.django_db
class TestValidateKeyCached:
    """Tests for AnthropicService.validate_key_cached()."""

    def setup_method(self):
        # Clear cache before each test
        AnthropicService._key_validation_cache.clear()

    @patch.object(AnthropicService, "test_connection")
    def test_cache_miss_calls_api(self, mock_test):
        mock_test.return_value = (True, "Connection successful")
        is_valid, error = AnthropicService.validate_key_cached("sk-new-key")
        assert is_valid is True
        assert error is None
        mock_test.assert_called_once_with("sk-new-key")

    @patch.object(AnthropicService, "test_connection")
    def test_cache_hit_skips_api(self, mock_test):
        """Second call within TTL uses cache."""
        mock_test.return_value = (True, "Connection successful")

        # First call populates cache
        AnthropicService.validate_key_cached("sk-cached")
        # Second call should use cache
        is_valid, error = AnthropicService.validate_key_cached("sk-cached")

        assert is_valid is True
        assert error is None
        # Only called once (first call)
        mock_test.assert_called_once()

    @patch.object(AnthropicService, "test_connection")
    def test_cache_expired_calls_api_again(self, mock_test):
        """Expired cache entry triggers new API call."""
        mock_test.return_value = (True, "Connection successful")

        # Populate cache with expired entry
        key_hash = hash("sk-expired")
        expired_time = time.time() - AnthropicService.KEY_VALIDATION_TTL - 1
        AnthropicService._key_validation_cache[key_hash] = (True, expired_time)

        is_valid, error = AnthropicService.validate_key_cached("sk-expired")
        assert is_valid is True
        mock_test.assert_called_once()

    @patch.object(AnthropicService, "test_connection")
    def test_invalid_key_cached(self, mock_test):
        mock_test.return_value = (False, "Invalid API key")
        is_valid, error = AnthropicService.validate_key_cached("sk-invalid")
        assert is_valid is False
        assert error == "Invalid API key"

    def test_no_key_returns_false(self):
        """No API key returns False without calling API."""
        with patch("apps.ai.services.anthropic_client.AppSettings") as mock_settings:
            mock_settings.get.return_value = MagicMock(anthropic_api_key="")
            is_valid, error = AnthropicService.validate_key_cached(None)
            assert is_valid is False
            assert "No API key" in error

    @patch.object(AnthropicService, "test_connection")
    def test_cached_invalid_returns_error_message(self, mock_test):
        """Cached invalid key returns proper error on subsequent calls."""
        mock_test.return_value = (False, "API key is invalid or expired")

        # First call
        AnthropicService.validate_key_cached("sk-bad")
        # Second call from cache
        is_valid, error = AnthropicService.validate_key_cached("sk-bad")
        assert is_valid is False
        assert error == "API key is invalid or expired"


# --- invalidate_key_cache() ---


class TestInvalidateKeyCache:
    """Tests for AnthropicService.invalidate_key_cache()."""

    def test_clears_cache(self):
        AnthropicService._key_validation_cache[12345] = (True, time.time())
        assert len(AnthropicService._key_validation_cache) > 0
        AnthropicService.invalidate_key_cache()
        assert len(AnthropicService._key_validation_cache) == 0

    def test_clears_empty_cache(self):
        """Clearing an already empty cache doesn't raise."""
        AnthropicService._key_validation_cache.clear()
        AnthropicService.invalidate_key_cache()
        assert len(AnthropicService._key_validation_cache) == 0


# --- get_available_models() ---


@pytest.mark.django_db
class TestGetAvailableModels:
    """Tests for AnthropicService.get_available_models()."""

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_returns_sorted_models(self, mock_anthropic_cls):
        mock_model_a = MagicMock()
        mock_model_a.id = "claude-opus-5-5"
        mock_model_a.display_name = "Claude Opus 5.5"
        mock_model_b = MagicMock()
        mock_model_b.id = "claude-sonnet-5-5"
        mock_model_b.display_name = "Claude Sonnet 5.5"

        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_response = MagicMock()
        mock_response.data = [mock_model_b, mock_model_a]  # unsorted
        mock_client.models.list.return_value = mock_response

        service = AnthropicService(api_key="sk-test")
        models = service.get_available_models()

        assert len(models) == 2
        # Should be sorted by name (case-insensitive)
        assert models[0]["name"] == "Claude Opus 5.5"
        assert models[1]["name"] == "Claude Sonnet 5.5"

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_invalid_response_raises(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.models.list.return_value = None

        service = AnthropicService(api_key="sk-test")
        with pytest.raises(AIResponseError, match="Invalid response"):
            service.get_available_models()

    @patch("apps.ai.services.anthropic_client.anthropic.Anthropic")
    def test_api_exception_raises(self, mock_anthropic_cls):
        mock_client = MagicMock()
        mock_anthropic_cls.return_value.__enter__ = MagicMock(return_value=mock_client)
        mock_anthropic_cls.return_value.__exit__ = MagicMock(return_value=False)
        mock_client.models.list.side_effect = RuntimeError("API down")

        service = AnthropicService(api_key="sk-test")
        with pytest.raises(AIResponseError, match="Failed to fetch"):
            service.get_available_models()


# --- is_available() ---


@pytest.mark.django_db
class TestIsAvailable:
    """Tests for AnthropicService.is_available()."""

    def test_available_with_key(self):
        with patch("apps.ai.services.anthropic_client.AppSettings") as mock_settings:
            mock_settings.get.return_value = MagicMock(anthropic_api_key="sk-present")
            assert AnthropicService.is_available() is True

    def test_unavailable_without_key(self):
        with patch("apps.ai.services.anthropic_client.AppSettings") as mock_settings:
            mock_settings.get.return_value = MagicMock(anthropic_api_key="")
            assert AnthropicService.is_available() is False
