"""Tests that a logged-out session cookie cannot re-authenticate (FR-005, FR-006)."""

import pytest
from django.contrib.auth import get_user_model

from apps.profiles.models import Profile

User = get_user_model()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


def _create_passkey_user(username="replay_user"):
    user = User.objects.create_user(username=username, password="!", is_active=True, is_staff=False)
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login(client, user):
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()


@pytest.mark.django_db
class TestPasskeyLogoutReplay:
    """After POST /api/auth/logout/, a replayed session cookie must be rejected."""

    def test_logged_out_cookie_cannot_hit_auth_me(self, client, passkey_mode):
        user = _create_passkey_user()
        _login(client, user)

        response = client.get("/api/auth/me/")
        assert response.status_code == 200

        client.post("/api/auth/logout/")

        response = client.get("/api/auth/me/")
        assert response.status_code == 401

    def test_logged_out_cookie_cannot_hit_recipes_favorites(self, client, passkey_mode):
        user = _create_passkey_user("fav_user")
        _login(client, user)

        client.post("/api/auth/logout/")

        response = client.get("/api/recipes/favorites/")
        assert response.status_code == 401
