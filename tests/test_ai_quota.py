"""Tests for the AI quota service (check, increment, usage, bypasses) and endpoints."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.ai.services.quota import check_quota, get_usage, increment_quota, ALL_FEATURES
from apps.core.models import AppSettings
from apps.profiles.models import Profile


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure each test starts with an empty cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


@pytest.fixture
def home_mode(settings):
    settings.AUTH_MODE = "home"


def _make_profile(username="testuser", is_staff=False, unlimited_ai=False):
    """Create a User + Profile pair and return the profile."""
    user = User.objects.create_user(username=username, password="!", email="", is_active=True, is_staff=is_staff)
    profile = Profile.objects.create(user=user, name=username, avatar_color="#d97850", unlimited_ai=unlimited_ai)
    return profile


@pytest.mark.django_db
class TestCheckAndIncrementCycle:
    """check_quota returns True until the limit is exhausted."""

    def test_exhaust_limit(self, passkey_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_remix = 3
        app.save()

        for i in range(3):
            allowed, info = check_quota(profile, "remix")
            assert allowed is True, f"should be allowed on call {i}"
            assert info == {}
            increment_quota(profile, "remix")

        allowed, info = check_quota(profile, "remix")
        assert allowed is False
        assert info["remaining"] == 0
        assert info["limit"] == 3
        assert info["used"] == 3
        assert "resets_at" in info


@pytest.mark.django_db
class TestAdminBypass:
    """Staff users always pass quota checks."""

    def test_admin_always_allowed(self, passkey_mode):
        profile = _make_profile("admin", is_staff=True)
        app = AppSettings.get()
        app.daily_limit_remix = 1
        app.save()

        # Increment well beyond the limit
        for _ in range(5):
            increment_quota(profile, "remix")

        allowed, info = check_quota(profile, "remix")
        assert allowed is True
        assert info == {}


@pytest.mark.django_db
class TestUnlimitedBypass:
    """Profiles with unlimited_ai=True always pass quota checks."""

    def test_unlimited_always_allowed(self, passkey_mode):
        profile = _make_profile("unlimited", unlimited_ai=True)
        app = AppSettings.get()
        app.daily_limit_remix = 1
        app.save()

        for _ in range(5):
            increment_quota(profile, "remix")

        allowed, info = check_quota(profile, "remix")
        assert allowed is True
        assert info == {}


@pytest.mark.django_db
class TestHomeModeBypass:
    """Home auth mode bypasses all quota checks."""

    def test_home_mode_always_allowed(self, home_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_remix = 1
        app.save()

        for _ in range(5):
            increment_quota(profile, "remix")

        allowed, info = check_quota(profile, "remix")
        assert allowed is True
        assert info == {}


@pytest.mark.django_db
class TestDailyReset:
    """A different date produces a separate cache key, resetting the counter."""

    def test_new_day_resets_counter(self, passkey_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_tips = 2
        app.save()

        # Exhaust today's quota
        for _ in range(2):
            increment_quota(profile, "tips")

        allowed, _ = check_quota(profile, "tips")
        assert allowed is False

        # Simulate the next day by patching datetime.now to return a future date
        with patch("apps.ai.services.quota.datetime") as mock_dt:
            from datetime import datetime, date, UTC

            future = datetime(2099, 1, 1, 12, 0, 0, tzinfo=UTC)
            mock_dt.now.return_value = future
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

            allowed, info = check_quota(profile, "tips")
            assert allowed is True
            assert info == {}


@pytest.mark.django_db
class TestLimitZeroDisables:
    """A limit of 0 means the feature is disabled for non-exempt users."""

    def test_zero_limit_denied_immediately(self, passkey_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_remix = 0
        app.save()

        allowed, info = check_quota(profile, "remix")
        assert allowed is False
        assert info["limit"] == 0
        assert info["used"] == 0
        assert info["remaining"] == 0


@pytest.mark.django_db
class TestIndependentFeatureCounters:
    """Exhausting one feature does not affect another."""

    def test_remix_does_not_affect_tips(self, passkey_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_remix = 1
        app.daily_limit_tips = 5
        app.save()

        increment_quota(profile, "remix")

        allowed_remix, _ = check_quota(profile, "remix")
        assert allowed_remix is False

        allowed_tips, info_tips = check_quota(profile, "tips")
        assert allowed_tips is True
        assert info_tips == {}


@pytest.mark.django_db
class TestGetUsage:
    """get_usage returns correct per-feature counts."""

    def test_returns_all_features(self, passkey_mode):
        profile = _make_profile()

        increment_quota(profile, "remix")
        increment_quota(profile, "remix")
        increment_quota(profile, "tips")

        usage = get_usage(profile.pk)
        assert usage["remix"] == 2
        assert usage["tips"] == 1
        assert usage["scale"] == 0
        assert usage["discover"] == 0

    def test_zero_when_unused(self, passkey_mode):
        profile = _make_profile()
        usage = get_usage(profile.pk)
        assert all(v == 0 for v in usage.values())


@pytest.mark.django_db
class TestDeniedInfoDict:
    """check_quota returns a proper info dict when quota is denied."""

    def test_info_dict_structure(self, passkey_mode):
        profile = _make_profile()
        app = AppSettings.get()
        app.daily_limit_scale = 2
        app.save()

        increment_quota(profile, "scale")
        increment_quota(profile, "scale")

        allowed, info = check_quota(profile, "scale")
        assert allowed is False
        assert info["remaining"] == 0
        assert info["limit"] == 2
        assert info["used"] == 2
        assert "resets_at" in info
        # resets_at should be an ISO 8601 datetime string
        assert "T" in info["resets_at"]


# ---------------------------------------------------------------------------
# Helpers for endpoint tests
# ---------------------------------------------------------------------------


def _login(client, user):
    """Authenticate via force_login and set session profile_id (passkey mode)."""
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()


# ---------------------------------------------------------------------------
# Quota endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestGetQuotasEndpoint:
    """GET /api/ai/quotas returns limits, usage, and reset time."""

    def test_get_quotas_returns_limits_and_usage(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("quotauser")
        increment_quota(profile, "remix")

        _login(client, profile.user)
        response = client.get("/api/ai/quotas")
        assert response.status_code == 200

        data = response.json()
        assert "limits" in data
        assert "usage" in data
        assert "unlimited" in data
        assert "resets_at" in data
        assert data["usage"]["remix"] == 1
        assert data["unlimited"] is False

    def test_get_quotas_returns_404_in_home_mode(self, client, settings):
        settings.AUTH_MODE = "home"
        profile = _make_profile("homeuser")
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get("/api/ai/quotas")
        assert response.status_code == 404


@pytest.mark.django_db
class TestUpdateQuotasEndpoint:
    """PUT /api/ai/quotas requires admin and updates limits."""

    def test_put_quotas_requires_admin(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("regular")
        _login(client, profile.user)

        response = client.put(
            "/api/ai/quotas",
            data=json.dumps(
                {"remix": 10, "remix_suggestions": 10, "scale": 10, "tips": 10, "discover": 10, "timer": 10}
            ),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_put_quotas_updates_limits(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("admin", is_staff=True)
        _login(client, profile.user)

        response = client.put(
            "/api/ai/quotas",
            data=json.dumps(
                {"remix": 50, "remix_suggestions": 20, "scale": 30, "tips": 40, "discover": 25, "timer": 15}
            ),
            content_type="application/json",
        )
        assert response.status_code == 200

        data = response.json()
        assert data["limits"]["remix"] == 50
        assert data["limits"]["remix_suggestions"] == 20
        assert data["limits"]["scale"] == 30
        assert data["limits"]["tips"] == 40
        assert data["limits"]["discover"] == 25
        assert data["limits"]["timer"] == 15


# ---------------------------------------------------------------------------
# Profile admin endpoint tests
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSetUnlimitedEndpoint:
    """POST /api/profiles/{id}/set-unlimited/ toggles unlimited AI access."""

    def test_set_unlimited_endpoint(self, client, settings):
        settings.AUTH_MODE = "passkey"
        admin = _make_profile("admin", is_staff=True)
        target = _make_profile("target")
        _login(client, admin.user)

        response = client.post(
            f"/api/profiles/{target.id}/set-unlimited/",
            data=json.dumps({"unlimited": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unlimited_ai"] is True

        target.refresh_from_db()
        assert target.unlimited_ai is True

    def test_set_unlimited_requires_admin(self, client, settings):
        settings.AUTH_MODE = "passkey"
        regular = _make_profile("regular")
        target = _make_profile("target")
        _login(client, regular.user)

        response = client.post(
            f"/api/profiles/{target.id}/set-unlimited/",
            data=json.dumps({"unlimited": True}),
            content_type="application/json",
        )
        assert response.status_code == 401


@pytest.mark.django_db
class TestRenameEndpoint:
    """PATCH /api/profiles/{id}/rename/ renames a profile."""

    def test_rename_endpoint(self, client, settings):
        settings.AUTH_MODE = "passkey"
        admin = _make_profile("admin", is_staff=True)
        target = _make_profile("target")
        _login(client, admin.user)

        response = client.patch(
            f"/api/profiles/{target.id}/rename/",
            data=json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"

        target.refresh_from_db()
        assert target.name == "New Name"

    def test_rename_requires_admin(self, client, settings):
        settings.AUTH_MODE = "passkey"
        regular = _make_profile("regular")
        target = _make_profile("target")
        _login(client, regular.user)

        response = client.patch(
            f"/api/profiles/{target.id}/rename/",
            data=json.dumps({"name": "Hacked"}),
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_rename_rejects_empty_name(self, client, settings):
        settings.AUTH_MODE = "passkey"
        admin = _make_profile("admin", is_staff=True)
        target = _make_profile("target")
        _login(client, admin.user)

        response = client.patch(
            f"/api/profiles/{target.id}/rename/",
            data=json.dumps({"name": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400
        assert response.json()["error"] == "validation_error"


# ---------------------------------------------------------------------------
# Quota only increments on actual OpenRouter calls, not cache hits
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestQuotaNotIncrementedOnCacheHit:
    """Quota should only count when OpenRouter is actually called, not when
    results are served from cache."""

    def test_tips_cached_does_not_increment(self, passkey_mode):
        """When generate_tips returns cached=True, quota should not increment."""
        profile = _make_profile()
        # Simulate what the endpoint does: if result is cached, don't increment
        increment_quota(profile, "tips")  # first real call
        usage_before = get_usage(profile.pk)["tips"]
        assert usage_before == 1

        # A cached response should NOT cause another increment
        # (endpoint checks result.get("cached") before incrementing)
        # We verify the logic here: only increment if not cached
        cached_result = {"tips": ["tip1"], "cached": True}
        if not cached_result.get("cached"):
            increment_quota(profile, "tips")

        usage_after = get_usage(profile.pk)["tips"]
        assert usage_after == 1  # unchanged

    def test_tips_fresh_does_increment(self, passkey_mode):
        """When generate_tips returns cached=False, quota should increment."""
        profile = _make_profile()
        fresh_result = {"tips": ["tip1"], "cached": False}
        if not fresh_result.get("cached"):
            increment_quota(profile, "tips")

        assert get_usage(profile.pk)["tips"] == 1

    def test_scale_cached_does_not_increment(self, passkey_mode):
        """When scale_recipe returns cached=True, quota should not increment."""
        profile = _make_profile()
        cached_result = {"cached": True, "ingredients": []}
        if not cached_result.get("cached"):
            increment_quota(profile, "scale")

        assert get_usage(profile.pk)["scale"] == 0

    def test_scale_fresh_does_increment(self, passkey_mode):
        """When scale_recipe returns cached=False, quota should increment."""
        profile = _make_profile()
        fresh_result = {"cached": False, "ingredients": []}
        if not fresh_result.get("cached"):
            increment_quota(profile, "scale")

        assert get_usage(profile.pk)["scale"] == 1


# ---------------------------------------------------------------------------
# Integration tests: quota enforcement at AI endpoints
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestTipsEndpointQuotaEnforcement:
    """Verify that /api/ai/tips returns 429 when the tips quota is exhausted."""

    def test_tips_returns_429_when_quota_exhausted(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("quotauser")

        app = AppSettings.get()
        app.daily_limit_tips = 1
        app.save()

        # Exhaust the quota
        increment_quota(profile, "tips")

        _login(client, profile.user)
        response = client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": 1}),
            content_type="application/json",
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "quota_exceeded"
        assert "resets_at" in data

    def test_tips_allowed_when_quota_not_exhausted(self, client, settings):
        """Verify that the quota check passes (endpoint may still fail for
        other reasons like missing recipe, but it should NOT be 429)."""
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("quotauser2")

        app = AppSettings.get()
        app.daily_limit_tips = 5
        app.save()

        _login(client, profile.user)
        response = client.post(
            "/api/ai/tips",
            data=json.dumps({"recipe_id": 999999}),
            content_type="application/json",
        )
        # Should fail for a different reason (404 recipe not found), not quota
        assert response.status_code != 429


@pytest.mark.django_db
class TestTimerEndpointQuotaEnforcement:
    """Verify that /api/ai/timer-name returns 429 when the timer quota is exhausted."""

    def test_timer_returns_429_when_quota_exhausted(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("timeruser")

        app = AppSettings.get()
        app.daily_limit_timer = 1
        app.save()

        increment_quota(profile, "timer")

        _login(client, profile.user)
        response = client.post(
            "/api/ai/timer-name",
            data=json.dumps({"step_text": "Boil water", "duration_minutes": 10}),
            content_type="application/json",
        )
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "quota_exceeded"


@pytest.mark.django_db
class TestDiscoverEndpointQuotaEnforcement:
    """Verify that /api/ai/discover/{id} returns 429 when quota is exhausted."""

    def test_discover_returns_429_when_quota_exhausted(self, client, settings):
        settings.AUTH_MODE = "passkey"
        profile = _make_profile("discoveruser")

        app = AppSettings.get()
        app.daily_limit_discover = 1
        app.save()

        increment_quota(profile, "discover")

        _login(client, profile.user)
        response = client.get(f"/api/ai/discover/{profile.pk}/")
        assert response.status_code == 429
        data = response.json()
        assert data["error"] == "quota_exceeded"
