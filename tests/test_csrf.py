"""
Tests for CSRF protection (T006b / T008).

In Django Ninja 1.6, CSRF is enforced through the SessionAuth mechanism:
- SessionAuth extends APIKeyCookie which has csrf=True by default
- When an endpoint uses auth=SessionAuth(), CSRF is validated via check_csrf()
- The CSRF token must be provided in the X-CSRFToken header

These tests verify that authenticated endpoints enforce CSRF tokens
and reject requests without valid CSRF credentials.
"""

import json

import pytest
from django.test import Client

from apps.profiles.models import Profile


@pytest.fixture
def csrf_client():
    """Client with CSRF checks enforced."""
    return Client(enforce_csrf_checks=True)


@pytest.fixture
def test_profile(db):
    """Create a test profile."""
    return Profile.objects.create(name="Test User", avatar_color="#d97850")


def _get_csrf_token(client):
    """Obtain a CSRF token via the public mode endpoint.

    Hits /api/system/mode/ which calls Django's get_token(), setting the
    csrftoken cookie exactly as the real frontend would receive it.
    Returns the token value from the cookie.
    """
    client.get("/api/system/mode/")
    return client.cookies["csrftoken"].value


@pytest.mark.django_db
class TestCsrfOnAuthenticatedEndpoints:
    """CSRF token must be required on endpoints protected by SessionAuth.

    SessionAuth extends APIKeyCookie which has csrf=True by default.
    When an endpoint uses auth=SessionAuth(), CSRF is checked automatically.
    """

    def test_post_without_csrf_token_returns_403(self, csrf_client, test_profile):
        """Authenticated POST without CSRF token is rejected.

        Even with a valid session, the request should fail if no CSRF token
        is provided, because SessionAuth enforces CSRF.
        """
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        response = csrf_client.post(
            "/api/system/reset/",
            data=json.dumps({"confirmation_text": "RESET"}),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_post_with_valid_csrf_token_succeeds(self, csrf_client, test_profile):
        """Authenticated POST with valid CSRF token does not return 403.

        Provide the CSRF token via X-CSRFToken header and csrftoken cookie.
        """
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        token = _get_csrf_token(csrf_client)

        # POST with CSRF token in header -- should not be rejected for CSRF
        # (may return 400 for bad confirmation, which is fine)
        response = csrf_client.post(
            "/api/system/reset/",
            data=json.dumps({"confirmation_text": "wrong"}),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )
        assert response.status_code != 403

    def test_invalid_csrf_token_returns_403(self, csrf_client, test_profile):
        """Authenticated POST with invalid CSRF token is rejected with 403."""
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        # Set a valid cookie but send a different token in the header
        _get_csrf_token(csrf_client)

        response = csrf_client.post(
            "/api/system/reset/",
            data=json.dumps({"confirmation_text": "RESET"}),
            content_type="application/json",
            headers={"X-CSRFToken": "invalid-token-value"},
        )
        assert response.status_code == 403

    def test_repair_selector_requires_csrf(self, csrf_client, test_profile):
        """POST /api/ai/repair-selector without CSRF token returns 403."""
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        response = csrf_client.post(
            "/api/ai/repair-selector",
            data=json.dumps(
                {
                    "source_id": 1,
                    "html_sample": "<div>test</div>",
                }
            ),
            content_type="application/json",
        )
        assert response.status_code == 403

    def test_multiple_endpoints_require_csrf(self, csrf_client, test_profile):
        """CSRF protection applies across all auth-protected POST endpoints."""
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        endpoints = [
            ("/api/system/reset/", {"confirmation_text": "RESET"}),
            ("/api/ai/repair-selector", {"source_id": 1, "html_sample": "<div>test</div>"}),
        ]
        for url, payload in endpoints:
            response = csrf_client.post(
                url,
                data=json.dumps(payload),
                content_type="application/json",
            )
            assert response.status_code == 403, f"Expected 403 for {url} without CSRF token, got {response.status_code}"


@pytest.mark.django_db
class TestCsrfWithValidToken:
    """Verify the full CSRF flow with token acquisition and submission."""

    def test_full_csrf_flow(self, csrf_client, test_profile):
        """Complete flow: set CSRF cookie -> POST with token -> not rejected."""
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        token = _get_csrf_token(csrf_client)

        # POST with CSRF token -- should pass CSRF validation
        response = csrf_client.post(
            "/api/system/reset/",
            data=json.dumps({"confirmation_text": "wrong"}),
            content_type="application/json",
            headers={"X-CSRFToken": token},
        )
        # Should not be 403 (CSRF rejection). 400 for bad confirmation is OK.
        assert response.status_code != 403

    def test_multiple_posts_with_same_token(self, csrf_client, test_profile):
        """CSRF token can be reused for multiple POST requests."""
        session = csrf_client.session
        session["profile_id"] = test_profile.id
        session.save()

        token = _get_csrf_token(csrf_client)

        # Multiple POSTs with same token should all pass CSRF
        for _ in range(3):
            response = csrf_client.post(
                "/api/system/reset/",
                data=json.dumps({"confirmation_text": "wrong"}),
                content_type="application/json",
                headers={"X-CSRFToken": token},
            )
            assert response.status_code != 403
