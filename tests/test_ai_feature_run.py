"""Tests for apps.ai.services.feature_run: the interface is the test surface.

Every reserve/refund path is exercised here once, against real quota counters.
"""

from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.ai.services.feature_run import (
    AIFeatureError,
    Ran,
    run_ai_feature,
    run_charged,
)
from apps.ai.services.quota import get_usage
from apps.core.models import AppSettings
from apps.profiles.models import Profile
from apps.recipes.models import Recipe

FEATURE = "remix"


@pytest.fixture(autouse=True)
def _passkey_quota(settings, db):
    settings.AUTH_MODE = "passkey"
    cache.clear()
    app = AppSettings.get()
    app.daily_limit_remix = 3
    app.save()
    yield
    cache.clear()


def _profile(name="alice"):
    user = User.objects.create_user(username=name, password="!", is_active=True)
    return Profile.objects.create(user=user, name=name, avatar_color="#d97850")


def _recipe(profile):
    return Recipe.objects.create(profile=profile, title="R", host="h", ingredients=["a"], instructions=["b"])


def _request(profile, limited=False):
    return SimpleNamespace(auth=profile, limited=limited, path="/api/ai/remix", META={"REMOTE_ADDR": "1.2.3.4"})


def _used(profile):
    return get_usage(profile.pk)[FEATURE]


class _Work:
    def __init__(self, result=None, exc=None):
        self.result, self.exc, self.calls = result, exc, 0

    def __call__(self, ctx=None):
        self.calls += 1
        if self.exc:
            raise self.exc
        return self.result


class TestRateLimitAndQuota:
    def test_rate_limited_never_reserves_or_works(self):
        p = _profile()
        work = _Work(Ran("x"))
        out = run_ai_feature(_request(p, limited=True), FEATURE, work)
        assert (out.status_code, out.value["error"]) == (429, "rate_limited")
        assert work.calls == 0 and _used(p) == 0

    def test_success_keeps_the_charge(self):
        p = _profile()
        assert run_ai_feature(_request(p), FEATURE, _Work(Ran({"ok": 1}))) == {"ok": 1}
        assert _used(p) == 1

    def test_quota_exhausted_is_429_with_info_and_no_work(self):
        p = _profile()
        for _ in range(3):
            run_ai_feature(_request(p), FEATURE, _Work(Ran("x")))
        work = _Work(Ran("x"))
        out = run_ai_feature(_request(p), FEATURE, work)
        assert out.status_code == 429
        assert out.value["error"] == "quota_exceeded"
        assert out.value["message"] == "Daily limit reached for remix"
        assert out.value["limit"] == 3 and out.value["remaining"] == 0
        assert work.calls == 0 and _used(p) == 3

    def test_home_mode_never_counts(self, settings):
        settings.AUTH_MODE = "home"
        p = _profile()
        run_ai_feature(_request(p), FEATURE, _Work(Ran("x", called_ai=False)))
        run_ai_feature(_request(p), FEATURE, _Work(Ran("x")))
        assert _used(p) == 0


class TestRefunds:
    def test_cache_hit_refunds(self):
        p = _profile()
        out = run_ai_feature(_request(p), FEATURE, _Work(Ran("cached", called_ai=False)))
        assert out == "cached" and _used(p) == 0

    def test_unexpected_exception_refunds_and_propagates(self):
        p = _profile()
        with pytest.raises(RuntimeError):
            run_ai_feature(_request(p), FEATURE, _Work(exc=RuntimeError("boom")))
        assert _used(p) == 0

    def test_expected_error_refunds_and_maps_to_status(self):
        p = _profile()
        out = run_ai_feature(
            _request(p), FEATURE, _Work(exc=AIFeatureError(400, "validation_error", "Duration must be positive"))
        )
        assert (out.status_code, out.value) == (
            400,
            {"error": "validation_error", "message": "Duration must be positive"},
        )
        assert _used(p) == 0

    def test_refund_only_returns_this_requests_slot(self):
        p = _profile()
        run_ai_feature(_request(p), FEATURE, _Work(Ran("x")))
        run_ai_feature(_request(p), FEATURE, _Work(Ran("x", called_ai=False)))
        assert _used(p) == 1


class TestOwnedRecipe:
    def test_owned_recipe_is_passed_to_work(self):
        p = _profile()
        r = _recipe(p)
        seen = {}

        def work(ctx):
            seen["ctx"] = ctx
            return Ran("ok")

        assert run_ai_feature(_request(p), FEATURE, work, recipe_id=r.id) == "ok"
        assert seen["ctx"].recipe == r and seen["ctx"].profile == p
        assert _used(p) == 1

    @pytest.mark.parametrize("which", ["missing", "other_profiles"])
    def test_missing_or_foreign_recipe_is_404_and_refunded(self, which):
        p = _profile()
        other = _profile("bob")
        rid = 99999 if which == "missing" else _recipe(other).id
        work = _Work(Ran("x"))
        out = run_ai_feature(_request(p), FEATURE, work, recipe_id=rid)
        assert (out.status_code, out.value) == (404, {"error": "not_found", "message": f"Recipe {rid} not found"})
        assert work.calls == 0 and _used(p) == 0

    def test_claimed_profile_must_match_the_authenticated_profile(self):
        p = _profile()
        r = _recipe(p)
        work = _Work(Ran("x"))
        out = run_ai_feature(_request(p), FEATURE, work, recipe_id=r.id, claimed_profile_id=p.id + 1000)
        assert out.status_code == 404
        assert out.value["message"] == f"Profile {p.id + 1000} not found"
        assert work.calls == 0 and _used(p) == 0

    def test_quota_and_ownership_use_the_same_profile(self):
        """The charged profile is the one ownership is checked against (request.auth)."""
        p = _profile()
        other = _profile("bob")
        run_ai_feature(_request(p), FEATURE, _Work(Ran("x")), recipe_id=_recipe(p).id)
        assert (_used(p), _used(other)) == (1, 0)


class TestRunCharged:
    def test_charge_false_neither_reserves_nor_refunds(self):
        p = _profile()
        run_charged(p, FEATURE, _Work(Ran("x")))  # used = 1
        assert run_charged(p, FEATURE, _Work(Ran("x", called_ai=False)), charge=False) == "x"
        with pytest.raises(RuntimeError):
            run_charged(p, FEATURE, _Work(exc=RuntimeError()), charge=False)
        assert _used(p) == 1

    def test_fallback_is_served_when_quota_is_exhausted(self):
        p = _profile()
        for _ in range(3):
            run_charged(p, FEATURE, _Work(Ran("x")))
        work = _Work(Ran("fresh"))
        assert run_charged(p, FEATURE, work, fallback=lambda: "stale") == "stale"
        assert work.calls == 0 and _used(p) == 3

    def test_exhausted_without_usable_fallback_is_429(self):
        p = _profile()
        for _ in range(3):
            run_charged(p, FEATURE, _Work(Ran("x")))
        assert run_charged(p, FEATURE, _Work(Ran("x")), fallback=lambda: None).status_code == 429
