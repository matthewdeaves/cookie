"""Concurrency tests for the AI quota service (pentest R16 F-31 regression).

Before these fixes:
- reserve_quota() used a non-atomic cache.set(key, 1) fallback when the key
  didn't exist, so concurrent first-time callers all clobbered each other
  back to 1 regardless of how many fired.
- PostgreSafeDatabaseCache.incr inherited Django's SELECT-then-UPDATE which
  races across connections — N concurrent incrs could settle at <N because
  each read the same pre-value and each wrote the same post-value.
- release_quota did not floor at zero, so the above races combined with
  cache-hit release calls could drive the counter negative. A negative
  counter silently bypasses the ``used >= limit`` check in check_quota.

These tests are in a separate file to keep test_ai_quota.py under its
grandfathered size ceiling.
"""

import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import connection

from apps.ai.services.quota import get_usage, release_quota, reserve_quota
from apps.core.models import AppSettings
from apps.profiles.models import Profile


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


def _make_profile(username: str) -> Profile:
    user = User.objects.create_user(username=username, password="!", email="", is_active=True)
    return Profile.objects.create(user=user, name=username, avatar_color="#d97850", unlimited_ai=False)


@pytest.mark.django_db
class TestReleaseFloorsAtZero:
    """release_quota must never leave the counter negative."""

    def test_release_on_absent_key_is_noop(self, passkey_mode):
        profile = _make_profile("absentrelease")
        release_quota(profile, "tips")
        assert get_usage(profile.pk)["tips"] == 0

    def test_release_floors_below_zero(self, passkey_mode):
        """If the counter is at 0 and release is called (unpaired), it must stay 0."""
        profile = _make_profile("zerorelease")
        key = f"ai_quota:{profile.pk}:tips:{datetime.now(UTC).date().isoformat()}"
        cache.set(key, 0, timeout=3600)
        release_quota(profile, "tips")
        assert get_usage(profile.pk)["tips"] == 0


@pytest.mark.django_db(transaction=True)
class TestConcurrentReserve:
    """Pentest R16 F-31 regression tests."""

    def test_concurrent_first_time_reserves_respect_limit(self, passkey_mode):
        """N threads racing on a fresh key must end with counter=LIMIT and
        exactly LIMIT allowed responses. Exercises the cache.add() atomic-init
        path AND the advisory-locked incr that together defeat the race."""
        profile = _make_profile("concurrent_reserve")
        app = AppSettings.get()
        app.daily_limit_tips = 3
        app.save()

        n = 10
        limit = 3
        barrier = threading.Barrier(n)

        def one_reserve():
            barrier.wait()
            try:
                allowed, _ = reserve_quota(profile, "tips")
                return allowed
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=n) as ex:
            results = list(ex.map(lambda _: one_reserve(), range(n)))

        assert results.count(True) == limit, (
            f"expected exactly {limit} allowed, got {results.count(True)}: {results}"
        )
        assert get_usage(profile.pk)["tips"] == limit

    def test_concurrent_reserve_release_pairs_do_not_go_negative(self, passkey_mode):
        """Simulates the pentest's concurrent cached /api/ai/tips scenario:
        each successful reserve is followed by a release (cache-hit path).
        The counter must never settle at a negative value."""
        profile = _make_profile("reserve_release_race")
        app = AppSettings.get()
        app.daily_limit_tips = 2
        app.save()

        n = 10
        barrier = threading.Barrier(n)

        def reserve_then_release():
            barrier.wait()
            try:
                allowed, _ = reserve_quota(profile, "tips")
                if allowed:
                    release_quota(profile, "tips")
                return allowed
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=n) as ex:
            list(ex.map(lambda _: reserve_then_release(), range(n)))

        assert get_usage(profile.pk)["tips"] >= 0, (
            f"tips quota went negative: {get_usage(profile.pk)['tips']}"
        )
