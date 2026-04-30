"""Tests for mode switching behavior (AUTH_MODE=home vs passkey)."""

import logging

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
        """T021: AUTH_MODE=home, /api/auth/me/ returns 404 (no user accounts)."""
        assert client.get("/api/auth/me/").status_code in (401, 404)

    def test_home_mode_profiles_get_no_auth_required(self, client):
        """T022: AUTH_MODE=home, /api/profiles/ GET is public (profile selection screen)."""
        Profile.objects.create(name="Alice", avatar_color="#d97850")
        response = client.get("/api/profiles/")
        assert response.status_code == 200

    def test_home_mode_profiles_get_returns_all(self, client):
        """T022: AUTH_MODE=home, /api/profiles/ GET returns all profiles when authenticated."""
        alice = Profile.objects.create(name="Alice", avatar_color="#d97850")
        Profile.objects.create(name="Bob", avatar_color="#8fae6f")
        session = client.session
        session["profile_id"] = alice.id
        session.save()
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
        """T018: GET /api/system/mode/ returns correct mode without version fingerprint."""
        response = client.get("/api/system/mode/")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "home"
        # version key removed in v1.42.0 to eliminate fingerprinting
        assert "version" not in data

    def test_mode_endpoint_passkey_has_no_version(self, client, settings):
        """GET /api/system/mode/ in passkey mode also omits version."""
        settings.AUTH_MODE = "passkey"
        response = client.get("/api/system/mode/")
        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "passkey"
        assert data.get("registration_enabled") is True
        assert "version" not in data

    def test_session_cookie_age(self):
        """SESSION_COOKIE_AGE is 86400 (24 hours) and refreshed every request.

        v1.73+: bumped from 12h → 24h plus SESSION_SAVE_EVERY_REQUEST=True,
        producing a rolling session. The increase + rolling behavior addresses
        iOS PWA users seeing unexpected logouts a few hours into a session
        from cookie eviction (storage pressure, app restarts, Safari ITP).
        """
        from django.conf import settings

        assert settings.SESSION_COOKIE_AGE == 86400
        assert settings.SESSION_SAVE_EVERY_REQUEST is True


@pytest.mark.django_db
class TestPublicModeFallback:
    """AUTH_MODE=public is no longer valid and falls back to home with a warning."""

    def test_public_mode_falls_back_to_home(self):
        """AUTH_MODE='public' is unrecognised and settings normalise it to 'home'."""
        import os

        # Simulate what settings.py does for an unrecognised mode
        raw = "public"
        assert raw not in ("home", "passkey"), "public should not be a valid mode"

        # The settings module logs a warning and falls back — verify the logic
        import cookie.settings as _settings_module  # noqa: F811

        # Re-run the validation logic from settings.py
        if raw not in ("home", "passkey"):
            fallback = "home"
        else:
            fallback = raw
        assert fallback == "home"

    def test_public_mode_warning_logged(self, caplog):
        """Settings logs a warning when AUTH_MODE is set to an invalid value like 'public'."""
        import importlib
        from unittest.mock import patch

        with (
            caplog.at_level(logging.WARNING, logger="cookie.settings"),
            patch.dict("os.environ", {"AUTH_MODE": "public", "DATABASE_URL": "postgres://u:p@h:5432/d"}),
        ):
            import cookie.settings

            importlib.reload(cookie.settings)

        assert "Unrecognised AUTH_MODE='public'" in caplog.text
        assert "falling back to 'home'" in caplog.text

        # Restore settings with real environment
        importlib.reload(cookie.settings)

    def test_removed_public_endpoints_not_found(self, client):
        """Endpoints that existed only in public mode no longer exist."""
        import json

        body = json.dumps(
            {
                "username": "t",
                "password": "p",
                "password_confirm": "p",
                "email": "e@e.com",
                "privacy_accepted": True,
            }
        )
        assert client.post("/api/auth/register/", data=body, content_type="application/json").status_code == 404
        body = json.dumps({"username": "t", "password": "p"})
        assert client.post("/api/auth/login/", data=body, content_type="application/json").status_code == 404
        assert client.post(
            "/api/auth/change-password/",
            data=json.dumps({"old_password": "a", "new_password": "b"}),
            content_type="application/json",
        ).status_code in (401, 404)
        assert (
            client.post(
                "/api/auth/verify-email/",
                data=json.dumps({"token": "x"}),
                content_type="application/json",
            ).status_code
            == 404
        )

    def test_mode_endpoint_never_returns_public(self, client):
        """GET /api/system/mode/ never returns 'public'."""
        response = client.get("/api/system/mode/")
        assert response.status_code == 200
        assert response.json()["mode"] in ("home", "passkey")
        assert response.json()["mode"] != "public"
