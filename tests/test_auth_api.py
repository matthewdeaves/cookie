"""Tests for apps/core/auth_api.py — logout and me endpoints (passkey mode)."""

import json

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.profiles.models import Profile


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_with_profile(db):
    """Create a User with an associated Profile."""
    user = User.objects.create_user(username="testuser", password="testpass123")  # pragma: allowlist secret
    profile = Profile.objects.create(
        user=user,
        name="Test User",
        avatar_color="#d97850",
        theme="dark",
        unit_preference="imperial",
    )
    return user, profile


@pytest.fixture
def passkey_auth_client(client, user_with_profile, settings):
    """Client logged in as a user with a profile, in passkey mode."""
    settings.AUTH_MODE = "passkey"
    user, profile = user_with_profile
    client.login(username="testuser", password="testpass123")  # pragma: allowlist secret
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


@pytest.mark.django_db
class TestLogoutView:
    """Tests for POST /api/auth/logout/."""

    def test_logout_success(self, passkey_auth_client):
        """Authenticated user can log out successfully."""
        response = passkey_auth_client.post("/api/auth/logout/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data == {"message": "Logged out successfully"}

    def test_logout_clears_session(self, passkey_auth_client):
        """Logout clears the user session so subsequent requests fail auth."""
        passkey_auth_client.post("/api/auth/logout/")
        response = passkey_auth_client.get("/api/auth/me/")
        assert response.status_code == 401

    def test_logout_requires_auth(self, client, settings):
        """Unauthenticated request to logout returns 401."""
        settings.AUTH_MODE = "passkey"
        response = client.post("/api/auth/logout/")
        assert response.status_code == 401

    def test_logout_returns_404_in_home_mode(self, client, user_with_profile, settings):
        """Logout endpoint returns 404 when in home mode.

        In home mode, SessionAuth authenticates via profile_id in session,
        so we set that up to pass auth, then _require_auth_mode raises 404.
        """
        settings.AUTH_MODE = "home"
        _user, profile = user_with_profile
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.post("/api/auth/logout/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestGetMe:
    """Tests for GET /api/auth/me/."""

    def test_get_me_success(self, passkey_auth_client, user_with_profile):
        """Authenticated user gets their profile info."""
        user, profile = user_with_profile
        response = passkey_auth_client.get("/api/auth/me/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["user"]["id"] == user.id
        assert data["user"]["is_admin"] is False
        assert data["profile"]["id"] == profile.id
        assert data["profile"]["name"] == "Test User"
        assert data["profile"]["avatar_color"] == "#d97850"
        assert data["profile"]["theme"] == "dark"
        assert data["profile"]["unit_preference"] == "imperial"

    def test_get_me_admin_user(self, client, db, settings):
        """Admin user has is_admin=True in response."""
        settings.AUTH_MODE = "passkey"
        admin = User.objects.create_user(
            username="admin",
            password="adminpass",  # pragma: allowlist secret
            is_staff=True,
        )
        profile = Profile.objects.create(user=admin, name="Admin", avatar_color="#aabbcc")
        client.login(username="admin", password="adminpass")  # pragma: allowlist secret
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/api/auth/me/")
        assert response.status_code == 200
        data = json.loads(response.content)
        assert data["user"]["is_admin"] is True

    def test_get_me_requires_auth(self, client, settings):
        """Unauthenticated request returns 401."""
        settings.AUTH_MODE = "passkey"
        response = client.get("/api/auth/me/")
        assert response.status_code == 401

    def test_get_me_returns_404_in_home_mode(self, client, user_with_profile, settings):
        """Me endpoint returns 404 when in home mode."""
        settings.AUTH_MODE = "home"
        _user, profile = user_with_profile
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/api/auth/me/")
        assert response.status_code == 404

    def test_get_me_user_without_profile(self, client, db, settings):
        """User without a profile gets 401 (SessionAuth rejects)."""
        settings.AUTH_MODE = "passkey"
        User.objects.create_user(username="noprofile", password="testpass")  # pragma: allowlist secret
        client.login(username="noprofile", password="testpass")  # pragma: allowlist secret
        response = client.get("/api/auth/me/")
        assert response.status_code == 401
