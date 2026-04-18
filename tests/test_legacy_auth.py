"""Tests for Legacy views authentication, passkey mode, and admin features."""

from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model

from apps.profiles.models import Profile
from apps.recipes.models import Recipe

User = get_user_model()


@pytest.mark.django_db
class TestLegacyPasskeyMode:
    """Tests for legacy views in passkey authentication mode."""

    @pytest.fixture
    def passkey_mode(self, settings):
        settings.AUTH_MODE = "passkey"

    @pytest.fixture
    def passkey_profile(self):
        user = User.objects.create_user(username="testuser", password="!", is_active=True)
        return Profile.objects.create(user=user, name="Test", avatar_color="#d97850")

    def test_require_profile_redirects_to_device_pair(self, client, passkey_mode):
        """In passkey mode, unauthenticated users redirect to device pairing."""
        response = client.get("/legacy/home/")
        assert response.status_code == 302
        assert response.url == "/legacy/pair/"

    def test_profile_selector_redirects_to_device_pair(self, client, passkey_mode):
        """In passkey mode, profile selector redirects to device pairing."""
        response = client.get("/legacy/")
        assert response.status_code == 302
        assert response.url == "/legacy/pair/"

    def test_require_profile_redirects_inactive_user(self, client, passkey_mode):
        """In passkey mode, inactive user is redirected to device pairing."""
        user = User.objects.create_user(username="inactive", password="!", is_active=False)
        profile = Profile.objects.create(user=user, name="Inactive", avatar_color="#d97850")

        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/legacy/home/")
        assert response.status_code == 302
        assert response.url == "/legacy/pair/"

    def test_require_profile_redirects_no_user(self, client, passkey_mode):
        """In passkey mode, profile without linked user is redirected."""
        profile = Profile.objects.create(name="NoUser", avatar_color="#d97850")

        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/legacy/home/")
        assert response.status_code == 302
        assert response.url == "/legacy/pair/"

    def test_require_profile_passkey_sees_no_admin_ui(self, client, passkey_mode):
        """In passkey mode the admin UI is hidden for ALL callers (spec 014-remove-is-staff).

        Operators manage via `python manage.py cookie_admin`. The settings page
        still loads (200), but admin-only blocks are template-gated by
        `{% if is_admin %}` which is derived from `auth_mode == "home"` only.
        """
        user = User.objects.create_user(username="user1", password="!", is_active=True)
        profile = Profile.objects.create(user=user, name="User1", avatar_color="#d97850")

        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/legacy/settings/")
        assert response.status_code == 200
        content = response.content.decode()
        # Admin-only quota config section is NOT rendered in passkey mode
        assert "quota-config-section" not in content

    def test_require_profile_non_staff_not_admin(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not see admin-only quota config."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        assert response.status_code == 200
        content = response.content.decode()
        # Admin-only quota config section is NOT rendered for regular users
        assert "quota-config-section" not in content

    def test_non_admin_cannot_see_admin_tab_buttons(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not see admin tab buttons."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert 'data-tab="general"' in content
        assert 'data-tab="prompts"' not in content
        assert 'data-tab="sources"' not in content
        assert 'data-tab="selectors"' not in content
        assert 'data-tab="users"' not in content
        assert 'data-tab="danger"' not in content

    def test_non_admin_cannot_see_admin_tab_content(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not see admin tab content."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert 'id="tab-prompts"' not in content
        assert 'id="tab-sources"' not in content
        assert 'id="tab-selectors"' not in content
        assert 'id="tab-users"' not in content
        assert 'id="tab-danger"' not in content

    def test_non_admin_cannot_see_api_key_section(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not see API key management."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert 'id="api-key-input"' not in content
        assert 'id="test-key-btn"' not in content
        assert 'id="save-key-btn"' not in content

    def test_non_admin_cannot_see_admin_modals(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not see admin modals."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert 'id="delete-profile-modal"' not in content
        assert 'id="reset-modal-step1"' not in content
        assert 'id="reset-modal-step2"' not in content

    def test_non_admin_does_not_load_admin_js(self, client, passkey_mode, passkey_profile):
        """In passkey mode, non-staff user does not load admin JS modules."""
        session = client.session
        session["profile_id"] = passkey_profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert "settings-core.js" in content
        assert "settings-general.js" in content
        assert "settings-prompts.js" not in content
        assert "settings-sources.js" not in content
        assert "settings-selectors.js" not in content
        assert "settings-users.js" not in content
        assert "settings-danger.js" not in content

    def test_passkey_user_sees_no_admin_tabs(self, client, passkey_mode):
        """Spec 014-remove-is-staff: passkey users are peers; zero admin UI.

        `is_admin` is derived purely from `auth_mode == "home"`. In passkey
        mode every `{% if is_admin %}` block is suppressed regardless of
        any per-user flag state.
        """
        user = User.objects.create_user(username="user2", password="!", is_active=True)
        profile = Profile.objects.create(user=user, name="User2", avatar_color="#d97850")

        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/legacy/settings/")
        content = response.content.decode()
        assert 'data-tab="prompts"' not in content
        assert 'data-tab="sources"' not in content
        assert 'data-tab="selectors"' not in content
        assert 'data-tab="users"' not in content
        assert 'data-tab="danger"' not in content
        assert 'id="tab-prompts"' not in content
        assert 'id="api-key-input"' not in content
        assert "settings-prompts.js" not in content


class TestLegacyRequireAdmin:
    """Tests for the require_admin decorator."""

    @pytest.fixture
    def passkey_mode(self, settings):
        settings.AUTH_MODE = "passkey"

    @pytest.fixture
    def _dummy_view(self):
        from apps.legacy.views import require_admin

        @require_admin
        def view(request):
            from django.http import HttpResponse

            return HttpResponse("ok")

        return view

    def test_require_admin_allows_in_home_mode(self, settings, _dummy_view):
        """In home mode, require_admin always allows access (no admin concept)."""
        from django.test import RequestFactory

        settings.AUTH_MODE = "home"
        request = RequestFactory().get("/")
        request.is_admin = False
        response = _dummy_view(request)
        assert response.status_code == 200

    def test_require_admin_redirects_non_admin_passkey(self, passkey_mode, _dummy_view):
        """In passkey mode, non-admin user is redirected to home."""
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.is_admin = False
        response = _dummy_view(request)
        assert response.status_code == 302
        assert response.url == "/legacy/home/"

    def test_require_admin_allows_admin_passkey(self, passkey_mode, _dummy_view):
        """In passkey mode, admin user can access."""
        from django.test import RequestFactory

        request = RequestFactory().get("/")
        request.is_admin = True
        response = _dummy_view(request)
        assert response.status_code == 200


@pytest.mark.django_db
class TestLegacyDevicePair:
    """Tests for the device pairing view."""

    def test_device_pair_redirects_in_home_mode(self, client, settings):
        """In home mode, device pair redirects to profile selector."""
        settings.AUTH_MODE = "home"
        response = client.get("/legacy/pair/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_device_pair_renders_in_passkey_mode(self, client, settings):
        """In passkey mode, device pair page renders."""
        settings.AUTH_MODE = "passkey"
        response = client.get("/legacy/pair/")
        assert response.status_code == 200


class TestLegacyAIAvailability:
    """Tests for _is_ai_available helper."""

    @patch("apps.legacy.views.OpenRouterService.validate_key_cached", return_value=(True, None))
    @patch("apps.legacy.views.AppSettings.get")
    def test_is_ai_available_with_valid_key(self, mock_settings, mock_validate):
        """_is_ai_available returns True when key is configured and valid."""
        from apps.legacy.views import _is_ai_available

        mock_settings.return_value.openrouter_api_key = "sk-test-key"  # pragma: allowlist secret
        assert _is_ai_available() is True
        mock_validate.assert_called_once()

    @patch("apps.legacy.views.OpenRouterService.validate_key_cached", return_value=(False, "invalid"))
    @patch("apps.legacy.views.AppSettings.get")
    def test_is_ai_available_with_invalid_key(self, mock_settings, mock_validate):
        """_is_ai_available returns False when key is invalid."""
        from apps.legacy.views import _is_ai_available

        mock_settings.return_value.openrouter_api_key = "sk-bad-key"  # pragma: allowlist secret
        assert _is_ai_available() is False


@pytest.mark.django_db
class TestLegacySettingsEdgeCases:
    """Tests for edge cases in the settings view."""

    @patch("apps.legacy.views.OpenRouterService")
    @patch("apps.legacy.views._is_ai_available", return_value=True)
    def test_settings_handles_ai_error(self, mock_ai, mock_service_cls, client):
        """Settings view renders with empty models list when AI service errors."""
        from apps.ai.services.openrouter import AIUnavailableError

        mock_service_cls.return_value.get_available_models.side_effect = AIUnavailableError("No key")

        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/settings/")
        assert response.status_code == 200
        # Verify the page rendered despite the AI error (no 500)
        content = response.content.decode()
        assert 'data-page="settings"' in content
