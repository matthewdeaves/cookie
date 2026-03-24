"""Tests for permission enforcement in public mode (T093-T105)."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.profiles.models import Profile


@pytest.fixture
def public_mode(settings):
    settings.AUTH_MODE = "public"


def _create_user(username, is_staff=False):
    user = User.objects.create_user(username=username, password="TestPass123!", email="", is_active=True, is_staff=is_staff)
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login(client, username):
    return client.post(
        "/api/auth/login/",
        data=json.dumps({"username": username, "password": "TestPass123!"}),
        content_type="application/json",
    )


@pytest.mark.django_db
class TestAdminEndpoints:
    """Non-admin gets 401 (auth denied) on admin endpoints."""

    def _setup_non_admin(self, client, public_mode):
        _create_user("admin", is_staff=True)
        _create_user("regular")
        _login(client, "regular")

    def test_system_reset_denied(self, client, public_mode):
        self._setup_non_admin(client, public_mode)
        response = client.post("/api/system/reset/", data=json.dumps({"confirmation_text": "RESET"}), content_type="application/json")
        assert response.status_code == 401

    def test_reset_preview_denied(self, client, public_mode):
        self._setup_non_admin(client, public_mode)
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 401

    def test_save_api_key_denied(self, client, public_mode):
        self._setup_non_admin(client, public_mode)
        response = client.post("/api/ai/save-api-key", data=json.dumps({"api_key": "test"}), content_type="application/json")
        assert response.status_code == 401


@pytest.mark.django_db
class TestProfileScoping:

    def test_profiles_returns_own_only(self, client, public_mode):
        _create_user("alice")
        _create_user("bob")
        _login(client, "alice")
        response = client.get("/api/profiles/")
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "alice"

    def test_admin_sees_all(self, client, public_mode):
        _create_user("admin", is_staff=True)
        _create_user("bob")
        _login(client, "admin")
        response = client.get("/api/profiles/")
        assert len(response.json()) == 2

    def test_create_profile_404(self, client, public_mode):
        _create_user("alice")
        _login(client, "alice")
        response = client.post("/api/profiles/", data=json.dumps({"name": "new"}), content_type="application/json")
        assert response.status_code == 404

    def test_select_profile_404(self, client, public_mode):
        user = _create_user("alice")
        _login(client, "alice")
        response = client.post(f"/api/profiles/{user.profile.id}/select/")
        assert response.status_code == 404
