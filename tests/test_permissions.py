"""Tests for permission enforcement in passkey mode (T093-T105)."""

import json

import pytest
from django.contrib.auth.models import User

from apps.profiles.models import Profile


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


def _create_user(username, is_staff=False):
    user = User.objects.create_user(username=username, password="!", email="", is_active=True, is_staff=is_staff)
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login(client, user):
    """Authenticate via force_login and set session profile_id (passkey mode)."""
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()


@pytest.mark.django_db
class TestAdminEndpoints:
    """Non-admin gets 403 (forbidden) on admin endpoints."""

    def _setup_non_admin(self, client, passkey_mode):
        _create_user("admin", is_staff=True)
        regular = _create_user("regular")
        _login(client, regular)

    def test_system_reset_denied(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.post(
            "/api/system/reset/", data=json.dumps({"confirmation_text": "RESET"}), content_type="application/json"
        )
        assert response.status_code == 403

    def test_reset_preview_denied(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 403

    def test_save_api_key_denied(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.post(
            "/api/ai/save-api-key", data=json.dumps({"api_key": "test"}), content_type="application/json"
        )
        assert response.status_code == 403


@pytest.mark.django_db
class TestProfileScoping:
    def test_profiles_returns_own_only(self, client, passkey_mode):
        alice = _create_user("alice")
        _create_user("bob")
        _login(client, alice)
        response = client.get("/api/profiles/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "alice"

    def test_admin_sees_all(self, client, passkey_mode):
        admin = _create_user("admin", is_staff=True)
        _create_user("bob")
        _login(client, admin)
        response = client.get("/api/profiles/")
        assert len(response.json()) == 2

    def test_create_profile_404(self, client, passkey_mode):
        alice = _create_user("alice")
        _login(client, alice)
        response = client.post("/api/profiles/", data=json.dumps({"name": "new"}), content_type="application/json")
        assert response.status_code == 404

    def test_select_profile_404(self, client, passkey_mode):
        alice = _create_user("alice")
        _login(client, alice)
        response = client.post(f"/api/profiles/{alice.profile.id}/select/")
        assert response.status_code == 404
