"""Tests for permission enforcement in passkey mode (T093-T105)."""

import json

import pytest
from django.contrib.auth.models import User

from apps.profiles.models import Profile
from apps.recipes.models import SearchSource


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


@pytest.fixture
def source(db):
    return SearchSource.objects.create(
        host="example.com",
        name="Example",
        search_url_template="https://example.com/search?q={query}",
        result_selector=".recipe-card",
    )


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
    """Admin endpoints 404 in passkey mode regardless of caller (HomeOnlyAdminAuth)."""

    def _setup_non_admin(self, client, passkey_mode):
        regular = _create_user("regular")
        _login(client, regular)

    def test_system_reset_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.post(
            "/api/system/reset/", data=json.dumps({"confirmation_text": "RESET"}), content_type="application/json"
        )
        assert response.status_code == 404

    def test_reset_preview_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.get("/api/system/reset-preview/")
        assert response.status_code == 404

    def test_save_api_key_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.post(
            "/api/ai/save-api-key", data=json.dumps({"api_key": "test"}), content_type="application/json"
        )
        assert response.status_code == 404

    def test_list_prompts_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.get("/api/ai/prompts")
        assert response.status_code == 404

    def test_get_prompt_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.get("/api/ai/prompts/tips_generation")
        assert response.status_code == 404

    def test_update_quotas_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.put(
            "/api/ai/quotas",
            data=json.dumps(
                {"remix": 99, "remix_suggestions": 99, "scale": 99, "tips": 99, "discover": 99, "timer": 99}
            ),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_cache_health_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode)
        response = client.get("/api/recipes/cache/health/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestAdminSourceEndpoints:
    """Source admin endpoints 404 in passkey mode (HomeOnlyAdminAuth)."""

    def _setup_non_admin(self, client, passkey_mode, source):
        regular = _create_user("regular")
        _login(client, regular)

    def test_toggle_source_404(self, client, passkey_mode, source):
        self._setup_non_admin(client, passkey_mode, source)
        response = client.post(f"/api/sources/{source.id}/toggle/")
        assert response.status_code == 404

    def test_bulk_toggle_404(self, client, passkey_mode, source):
        self._setup_non_admin(client, passkey_mode, source)
        response = client.post(
            "/api/sources/bulk-toggle/",
            data=json.dumps({"enable": False}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_update_selector_404(self, client, passkey_mode, source):
        self._setup_non_admin(client, passkey_mode, source)
        response = client.put(
            f"/api/sources/{source.id}/selector/",
            data=json.dumps({"result_selector": ".hacked"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_test_source_404(self, client, passkey_mode, source):
        self._setup_non_admin(client, passkey_mode, source)
        response = client.post(f"/api/sources/{source.id}/test/")
        assert response.status_code == 404

    def test_test_all_sources_404(self, client, passkey_mode):
        self._setup_non_admin(client, passkey_mode, None)
        response = client.post("/api/sources/test-all/")
        assert response.status_code == 404


@pytest.mark.django_db
class TestProfileScoping:
    """Spec 014-remove-is-staff FR-009: /api/profiles/ is 404 in passkey mode.

    Passkey users get their profile via /auth/me; there is no list-all endpoint.
    """

    def test_profiles_list_returns_404_for_authed_user(self, client, passkey_mode):
        alice = _create_user("alice")
        _create_user("bob")
        _login(client, alice)
        response = client.get("/api/profiles/")
        assert response.status_code == 404

    def test_profiles_list_returns_404_for_unauthed(self, client, passkey_mode):
        _create_user("alice")
        response = client.get("/api/profiles/")
        assert response.status_code == 404

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
