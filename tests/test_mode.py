"""Tests for mode switching behavior (AUTH_MODE=home vs public)."""

import pytest
from django.test import Client, override_settings

from apps.profiles.models import Profile


@pytest.mark.django_db
class TestHomeModeDefaults:
    """T020-T024: Home mode is default and runs identically to current behavior."""

    def test_home_mode_is_default(self):
        """T020: Home mode when AUTH_MODE not set."""
        from django.conf import settings

        assert settings.AUTH_MODE == "home"

    def test_home_mode_auth_endpoints_404(self, client):
        """T021: AUTH_MODE=home, /api/auth/* returns 404."""
        import json

        body = json.dumps({"username": "t", "password": "p", "password_confirm": "p", "email": "e@e.com", "privacy_accepted": True})
        assert client.post("/api/auth/register/", data=body, content_type="application/json").status_code == 404
        body = json.dumps({"username": "t", "password": "p"})
        assert client.post("/api/auth/login/", data=body, content_type="application/json").status_code == 404
        assert client.get("/api/auth/me/").status_code in (401, 404)  # 401 from auth check before mode check

    def test_home_mode_profiles_get_returns_all(self, client):
        """T022: AUTH_MODE=home, /api/profiles/ GET returns all profiles."""
        Profile.objects.create(name="Alice", avatar_color="#d97850")
        Profile.objects.create(name="Bob", avatar_color="#8fae6f")
        response = client.get("/api/profiles/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_home_mode_profiles_post_creates(self, client):
        """T023: AUTH_MODE=home, /api/profiles/ POST creates profile without registration."""
        import json

        response = client.post(
            "/api/profiles/",
            data=json.dumps({"name": "Charlie", "avatar_color": "#d97850"}),
            content_type="application/json",
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Charlie"

    def test_mode_endpoint_returns_home(self, client):
        """T018: GET /api/system/mode/ returns correct mode."""
        response = client.get("/api/system/mode/")
        assert response.status_code == 200
        assert response.json() == {"mode": "home"}

    def test_session_cookie_age(self):
        """T062b: SESSION_COOKIE_AGE remains 43200 (12 hours)."""
        from django.conf import settings

        assert settings.SESSION_COOKIE_AGE == 43200
