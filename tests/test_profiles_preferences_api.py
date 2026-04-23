"""
Round 10 theme-toggle fix: PATCH /api/profiles/{id}/preferences/.

This endpoint was added in v1.53.0 to let passkey-mode users flip dark-mode
and change unit preferences. Before v1.53.0 the frontend called
PUT /api/profiles/{id}/ which is HomeOnlyAuth-gated (404 in passkey mode).
That 404 was caught by the frontend toggleTheme handler, which rolled back
the optimistic UI — from the user's perspective the theme flickered to
dark and immediately flipped back to light on iPhone (where the user most
visibly used dark mode).

Split from tests/test_profiles_api.py so both files stay under the 500-line
constitutional cap. Helpers live in tests/_profile_test_helpers.py.
"""

import json

import pytest

from apps.profiles.models import Profile

from tests._profile_test_helpers import create_user as _create_user, login as _login


@pytest.mark.django_db
class TestUpdatePreferences:
    """Coverage matrix:

    - home mode: theme + unit, happy path
    - passkey mode: theme + unit, happy path (this was the bug)
    - auth: 401 when unauthenticated, 403 when updating someone else's profile
    - validation: 400 on bogus theme / unit, 200 no-op on empty payload
    - isolation: identity fields (name, avatar_color) are NOT writable here
    """

    def _patch(self, client, profile_id, data):
        return client.patch(
            f"/api/profiles/{profile_id}/preferences/",
            data=json.dumps(data),
            content_type="application/json",
        )

    def test_home_mode_theme_toggle(self, client):
        profile = Profile.objects.create(name="Home", avatar_color="#000")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = self._patch(client, profile.id, {"theme": "dark"})
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"
        profile.refresh_from_db()
        assert profile.theme == "dark"

    def test_passkey_mode_theme_toggle(self, client, settings):
        """THE ACTUAL BUG: pre-v1.53.0 PUT was HomeOnly → 404 in passkey.
        This endpoint uses SessionAuth so it works in both modes."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("darker")
        _login(client, user)
        response = self._patch(client, user.profile.id, {"theme": "dark"})
        assert response.status_code == 200
        assert response.json()["theme"] == "dark"

    def test_passkey_mode_unit_preference(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("imperial")
        _login(client, user)
        response = self._patch(client, user.profile.id, {"unit_preference": "imperial"})
        assert response.status_code == 200
        assert response.json()["unit_preference"] == "imperial"

    def test_combined_theme_and_unit(self, client, settings):
        """Single PATCH updates both fields atomically."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("both")
        _login(client, user)
        response = self._patch(
            client,
            user.profile.id,
            {"theme": "dark", "unit_preference": "imperial"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["theme"] == "dark"
        assert data["unit_preference"] == "imperial"

    def test_cross_profile_forbidden(self, client, settings):
        """Callers may only modify their OWN profile. No cross-user update."""
        settings.AUTH_MODE = "passkey"
        owner = _create_user("owner")
        attacker = _create_user("attacker")
        _login(client, attacker)
        response = self._patch(client, owner.profile.id, {"theme": "dark"})
        assert response.status_code == 403
        owner.profile.refresh_from_db()
        assert owner.profile.theme == "light"  # unchanged

    def test_unauthenticated_passkey_returns_401(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("target")
        response = self._patch(client, user.profile.id, {"theme": "dark"})
        assert response.status_code == 401

    def test_invalid_theme_rejected(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("t1")
        _login(client, user)
        response = self._patch(client, user.profile.id, {"theme": "rainbow"})
        assert response.status_code == 400

    def test_invalid_unit_rejected(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("t2")
        _login(client, user)
        response = self._patch(client, user.profile.id, {"unit_preference": "cubits"})
        assert response.status_code == 400

    def test_cannot_change_name_via_preferences(self, client, settings):
        """Regression guard: identity fields (name, avatar_color) MUST NOT
        be writable via the preferences endpoint even if smuggled in."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("identity")
        _login(client, user)
        original_name = user.profile.name
        # Pydantic schema drops unknown fields → name is ignored, not rejected.
        response = self._patch(
            client,
            user.profile.id,
            {"name": "Renamed", "theme": "dark"},
        )
        assert response.status_code == 200
        user.profile.refresh_from_db()
        assert user.profile.name == original_name  # unchanged
        assert user.profile.theme == "dark"  # allowed field did apply

    def test_empty_payload_is_noop(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("empty")
        _login(client, user)
        response = self._patch(client, user.profile.id, {})
        assert response.status_code == 200
        # No update happened — theme and unit still at their defaults.
        assert response.json()["theme"] == "light"

    def test_response_does_not_expose_is_admin(self, client, settings):
        """Regression guard for INFO-4 (R14): PATCH preferences must not expose
        the retired is_admin field. It was stripped from /auth/me in v1.43.0
        but the ProfileOut serializer used here still had it until this fix."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("noadmin")
        _login(client, user)
        response = self._patch(client, user.profile.id, {"theme": "dark"})
        assert response.status_code == 200
        assert "is_admin" not in response.json(), (
            "PATCH /profiles/{id}/preferences/ MUST NOT expose is_admin (retired in v1.43.0, spec 014-remove-is-staff)"
        )
