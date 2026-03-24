"""
Tests for rate limiting on AI key endpoints.

Verifies that POST /api/ai/test-api-key and POST /api/ai/save-api-key
are limited to 20/hour each.

Uses django-ratelimit which reads IP from HTTP_X_FORWARDED_FOR
(configured via RATELIMIT_IP_META_KEY in settings).
"""

import json
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.test import Client

from apps.profiles.models import Profile

FORWARDED_FOR_HEADER = {"HTTP_X_FORWARDED_FOR": "203.0.113.1"}


@pytest.fixture
def client():
    c = Client()
    profile = Profile.objects.create(name="Rate Limit Test")
    session = c.session
    session["profile_id"] = profile.id
    session.save()
    return c


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
    """Rate limiting on POST /api/ai/test-api-key (20/hour)."""

    @patch("apps.ai.api.OpenRouterService.test_connection")
    def test_allows_requests_within_limit(self, mock_test, client):
        """First 20 requests within the window should succeed."""
        mock_test.return_value = (True, "Valid key")

        for i in range(20):
            response = client.post(
                "/api/ai/test-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )
            assert response.status_code != 429, f"Request {i + 1} of 20 was rate-limited unexpectedly"

    @patch("apps.ai.api.OpenRouterService.test_connection")
    def test_blocks_21st_request(self, mock_test, client):
        """21st request within the window must return 429."""
        mock_test.return_value = (True, "Valid key")

        for _i in range(20):
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
    """Rate limiting on POST /api/ai/save-api-key (20/hour)."""

    @patch("apps.ai.api.OpenRouterService.invalidate_key_cache")
    def test_allows_requests_within_limit(self, mock_invalidate, client):
        """First 20 requests within the window should succeed."""
        for i in range(20):
            response = client.post(
                "/api/ai/save-api-key",
                data=json.dumps({"api_key": "sk-test-key"}),
                content_type="application/json",
                **FORWARDED_FOR_HEADER,
            )
            assert response.status_code != 429, f"Request {i + 1} of 20 was rate-limited unexpectedly"

    @patch("apps.ai.api.OpenRouterService.invalidate_key_cache")
    def test_blocks_21st_request(self, mock_invalidate, client):
        """21st request within the window must return 429."""
        for _i in range(20):
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
