"""
Tests for rate limiting on AI key endpoints (T006).

Verifies that POST /api/ai/test-api-key is limited to 5/hour
and POST /api/ai/save-api-key is limited to 3/hour.

Uses django-ratelimit which reads IP from HTTP_X_FORWARDED_FOR
(configured via RATELIMIT_IP_META_KEY in settings).
"""

import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client


FORWARDED_FOR_HEADER = {"HTTP_X_FORWARDED_FOR": "203.0.113.1"}


@pytest.fixture
def client():
    return Client()


@pytest.fixture(autouse=True)
def _enable_rate_limiting(settings):
    """Enable rate limiting for these tests and clear cache."""
    settings.RATELIMIT_ENABLE = True
    settings.RATELIMIT_IP_META_KEY = "HTTP_X_FORWARDED_FOR"
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
class TestTestApiKeyRateLimit:
    """Rate limiting on POST /api/ai/test-api-key (5/hour)."""

    @patch("apps.ai.api.OpenRouterService.test_connection")
    def test_allows_requests_within_limit(self, mock_test, client):
        """First 5 requests within the window should succeed."""
        mock_test.return_value = (True, "Valid key")

        for i in range(5):
            response = client.post(
                "/api/ai/test-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )
            assert response.status_code != 429, f"Request {i + 1} of 5 was rate-limited unexpectedly"

    @patch("apps.ai.api.OpenRouterService.test_connection")
    def test_blocks_6th_request(self, mock_test, client):
        """6th request within the window must return 429."""
        mock_test.return_value = (True, "Valid key")

        for _i in range(5):
            client.post(
                "/api/ai/test-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )

        response = client.post(
            "/api/ai/test-api-key",
            data=json.dumps({"api_key": "sk-test-key"}),
            content_type="application/json",
            **FORWARDED_FOR_HEADER,
        )
        assert response.status_code == 429


@pytest.mark.django_db
class TestSaveApiKeyRateLimit:
    """Rate limiting on POST /api/ai/save-api-key (3/hour)."""

    @patch("apps.ai.api.OpenRouterService.invalidate_key_cache")
    def test_allows_requests_within_limit(self, mock_invalidate, client):
        """First 3 requests within the window should succeed."""
        for i in range(3):
            response = client.post(
                "/api/ai/save-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )
            assert response.status_code != 429, f"Request {i + 1} of 3 was rate-limited unexpectedly"

    @patch("apps.ai.api.OpenRouterService.invalidate_key_cache")
    def test_blocks_4th_request(self, mock_invalidate, client):
        """4th request within the window must return 429."""
        for _i in range(3):
            client.post(
                "/api/ai/save-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )

        response = client.post(
            "/api/ai/save-api-key",
            data=json.dumps({"api_key": "sk-test-key"}),
            content_type="application/json",
            **FORWARDED_FOR_HEADER,
        )
        assert response.status_code == 429
