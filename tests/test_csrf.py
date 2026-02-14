"""Tests for Phase 12 Session G: CSRF Protection."""

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.core.models import AppSettings
from apps.profiles.models import Profile


class TestCSRF:
    """Tests for Session G - CSRF Protection."""

    @pytest.mark.django_db
    def test_login_requires_csrf_token(self, monkeypatch):
        """POST to login without CSRF token returns 403."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Use enforce_csrf_checks=True to test CSRF enforcement
        client = Client(enforce_csrf_checks=True)

        response = client.post(
            "/legacy/login/",
            {"username": "test", "password": "password"},  # pragma: allowlist secret
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_register_requires_csrf_token(self, monkeypatch):
        """POST to register without CSRF token returns 403."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client(enforce_csrf_checks=True)

        response = client.post(
            "/legacy/register/",
            {
                "username": "newuser",
                "password": "password123",  # pragma: allowlist secret
                "password_confirm": "password123",  # pragma: allowlist secret
                "avatar_color": "#FF5733",
            },
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_post_requires_csrf_token(self):
        """POST to Django Ninja API without CSRF returns 403."""
        # Create a profile to test with
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        client = Client(enforce_csrf_checks=True)

        # Try to select profile without CSRF token
        response = client.post(f"/api/profiles/{profile.id}/select/")

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_post_with_csrf_token_succeeds(self, monkeypatch):
        """POST to Django Ninja API with valid CSRF succeeds."""
        # Enable public mode so login page is accessible (needed for CSRF cookie)
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create a profile to test with
        profile = Profile.objects.create(name="Test", avatar_color="#FF5733")

        # Create a user linked to this profile for public mode
        user = User.objects.create_user(username="testuser", password="testpass123")
        profile.user = user
        profile.save()

        client = Client(enforce_csrf_checks=True)

        # First, make a GET request to login page to get CSRF cookie
        # (Pages with {% csrf_token %} set the CSRF cookie)
        response = client.get("/legacy/login/")
        assert response.status_code == 200

        # Extract CSRF token from cookies
        csrf_token = client.cookies.get("csrftoken")
        assert csrf_token is not None, "CSRF token should be set in cookie"

        # Login first (required in public mode)
        client.force_login(user)

        # Now make POST with CSRF token in header
        response = client.post(
            f"/api/profiles/{profile.id}/select/",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token.value,
        )

        assert response.status_code == 200
        assert response.json()["id"] == profile.id

    @pytest.mark.django_db
    def test_csrf_token_in_cookie(self, monkeypatch):
        """CSRF token is set in cookie after GET request to page with form."""
        # Enable public mode so login page is accessible
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client()

        # Make a GET request to a page with {% csrf_token %} in form
        # The login page has a form that includes the CSRF token
        response = client.get("/legacy/login/")
        assert response.status_code == 200

        # Check CSRF cookie is set
        csrf_token = client.cookies.get("csrftoken")
        assert csrf_token is not None, "CSRF token should be set in cookie"
        assert len(csrf_token.value) > 0, "CSRF token should not be empty"

    @pytest.mark.django_db
    def test_login_with_csrf_token_succeeds(self, monkeypatch):
        """POST to login with valid CSRF token succeeds (with valid credentials)."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        # Create user with profile
        user = User.objects.create_user(username="testuser", password="testpass123")
        Profile.objects.create(user=user, name="Test", avatar_color="#FF5733")

        client = Client(enforce_csrf_checks=True)

        # Get CSRF token via GET request
        response = client.get("/legacy/login/")
        assert response.status_code == 200

        csrf_token = client.cookies.get("csrftoken")
        assert csrf_token is not None

        # Login with CSRF token
        response = client.post(
            "/legacy/login/",
            {
                "username": "testuser",
                "password": "testpass123",  # pragma: allowlist secret
                "csrfmiddlewaretoken": csrf_token.value,
            },
        )

        # Should redirect on success
        assert response.status_code == 302
        assert "/legacy/home/" in response.url

    @pytest.mark.django_db
    def test_register_with_csrf_token_succeeds(self, monkeypatch):
        """POST to register with valid CSRF token succeeds."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        client = Client(enforce_csrf_checks=True)

        # Get CSRF token via GET request
        response = client.get("/legacy/register/")
        assert response.status_code == 200

        csrf_token = client.cookies.get("csrftoken")
        assert csrf_token is not None

        # Register with CSRF token
        response = client.post(
            "/legacy/register/",
            {
                "username": "newuser",
                "password": "password123",  # pragma: allowlist secret
                "password_confirm": "password123",  # pragma: allowlist secret
                "avatar_color": "#FF5733",
                "csrfmiddlewaretoken": csrf_token.value,
            },
        )

        # Should redirect on success
        assert response.status_code == 302
        assert "/legacy/home/" in response.url

        # Verify user was created
        assert User.objects.filter(username="newuser").exists()

    @pytest.mark.django_db
    def test_api_put_requires_csrf_token(self):
        """PUT to Django Ninja API without CSRF returns 403."""
        client = Client(enforce_csrf_checks=True)

        response = client.put(
            "/api/system/auth-settings/",
            data={"deployment_mode": "public"},
            content_type="application/json",
        )

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_delete_requires_csrf_token(self):
        """DELETE to Django Ninja API without CSRF returns 403."""
        # Create a profile to delete
        profile = Profile.objects.create(name="ToDelete", avatar_color="#FF5733")

        client = Client(enforce_csrf_checks=True)

        response = client.delete(f"/api/profiles/{profile.id}/")

        assert response.status_code == 403

    @pytest.mark.django_db
    def test_api_get_does_not_require_csrf(self):
        """GET requests do not require CSRF token."""
        client = Client(enforce_csrf_checks=True)

        # GET requests should work without CSRF
        response = client.get("/api/health")
        assert response.status_code == 200

        response = client.get("/api/system/auth-settings/")
        assert response.status_code == 200

    @pytest.mark.django_db
    def test_csrf_token_changes_after_login(self, monkeypatch):
        """CSRF token is rotated after login for security."""
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")

        user = User.objects.create_user(username="testuser", password="testpass123")
        Profile.objects.create(user=user, name="Test", avatar_color="#FF5733")

        client = Client(enforce_csrf_checks=True)

        # Get initial CSRF token
        client.get("/legacy/login/")
        initial_csrf = client.cookies.get("csrftoken").value

        # Login
        client.post(
            "/legacy/login/",
            {
                "username": "testuser",
                "password": "testpass123",  # pragma: allowlist secret
                "csrfmiddlewaretoken": initial_csrf,
            },
        )

        # CSRF token should be rotated after login
        new_csrf = client.cookies.get("csrftoken").value
        assert new_csrf != initial_csrf, "CSRF token should rotate after login"
