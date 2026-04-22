"""AI quota checking and tracking service.

Uses Django's database cache backend to enforce per-profile, per-feature
daily limits. Quotas only apply in passkey auth mode — home mode is unlimited.
"""

import logging
from datetime import datetime, timedelta, UTC

from django.conf import settings
from django.core.cache import cache

from apps.core.models import AppSettings

logger = logging.getLogger(__name__)

ALL_FEATURES = (
    "remix",
    "remix_suggestions",
    "scale",
    "tips",
    "discover",
    "timer",
)

FEATURE_LIMIT_FIELDS = {
    "remix": "daily_limit_remix",
    "remix_suggestions": "daily_limit_remix_suggestions",
    "scale": "daily_limit_scale",
    "tips": "daily_limit_tips",
    "discover": "daily_limit_discover",
    "timer": "daily_limit_timer",
}


def _cache_key(profile_id: int, feature: str) -> str:
    """Build the daily cache key for a profile/feature pair."""
    today = datetime.now(UTC).date()
    return f"ai_quota:{profile_id}:{feature}:{today.isoformat()}"


def _seconds_until_midnight_utc() -> int:
    """Return seconds remaining until the next UTC midnight."""
    now = datetime.now(UTC)
    tomorrow = datetime(now.year, now.month, now.day, tzinfo=UTC) + timedelta(days=1)
    return int((tomorrow - now).total_seconds())


def _next_midnight_utc_iso() -> str:
    """Return next UTC midnight as an ISO 8601 string."""
    now = datetime.now(UTC)
    tomorrow = datetime(now.year, now.month, now.day, tzinfo=UTC) + timedelta(days=1)
    return tomorrow.isoformat()


def check_quota(profile, feature: str) -> tuple[bool, dict]:
    """Check whether *profile* may use *feature* right now (read-only).

    Returns (allowed, info_dict). Info is empty when allowed;
    contains remaining/limit/used/resets_at when denied.

    NOTE: For atomic enforcement under concurrent load, use
    reserve_quota() instead of check_quota() + increment_quota().
    """
    if getattr(settings, "AUTH_MODE", "home") != "passkey":
        return (True, {})

    if profile.unlimited_ai:
        return (True, {})

    if feature not in FEATURE_LIMIT_FIELDS:
        raise ValueError(f"Unknown quota feature: {feature}")

    app = AppSettings.get()
    limit_field = FEATURE_LIMIT_FIELDS[feature]
    limit = getattr(app, limit_field)

    key = _cache_key(profile.pk, feature)
    used = cache.get(key, 0)

    if used >= limit:
        return (
            False,
            {
                "remaining": 0,
                "limit": limit,
                "used": used,
                "resets_at": _next_midnight_utc_iso(),
            },
        )

    return (True, {})


def reserve_quota(profile, feature: str) -> tuple[bool, dict]:
    """Atomically reserve a quota slot BEFORE executing the AI operation.

    Uses cache.incr() which is atomic at the database level, preventing
    concurrent requests from bypassing the quota limit.

    Returns (allowed, info_dict). If allowed, the counter is already
    incremented. On AI failure, call release_quota() to roll back.
    """
    if getattr(settings, "AUTH_MODE", "home") != "passkey":
        return (True, {})

    if profile.unlimited_ai:
        return (True, {})

    if feature not in FEATURE_LIMIT_FIELDS:
        raise ValueError(f"Unknown quota feature: {feature}")

    app = AppSettings.get()
    limit_field = FEATURE_LIMIT_FIELDS[feature]
    limit = getattr(app, limit_field)

    key = _cache_key(profile.pk, feature)
    ttl = _seconds_until_midnight_utc()

    # Atomic increment — if key doesn't exist, set to 1
    try:
        new_count = cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=ttl)
        new_count = 1

    if new_count > limit:
        # Over limit — roll back the increment we just did
        try:
            cache.decr(key)
        except ValueError:
            pass
        return (
            False,
            {
                "remaining": 0,
                "limit": limit,
                "used": new_count - 1,
                "resets_at": _next_midnight_utc_iso(),
            },
        )

    return (True, {})


def release_quota(profile, feature: str) -> None:
    """Roll back a reserved quota slot on AI operation failure (FR-009)."""
    if getattr(settings, "AUTH_MODE", "home") != "passkey":
        return
    if profile.unlimited_ai:
        return

    key = _cache_key(profile.pk, feature)
    try:
        cache.decr(key)
    except ValueError:
        logger.debug("quota release: cache key missing for profile=%s feature=%s (cache may have been flushed)", profile.pk, feature)


def increment_quota(profile, feature: str) -> None:
    """Increment the daily counter after a successful AI operation.

    DEPRECATED: Use reserve_quota() / release_quota() instead for
    atomic enforcement under concurrent load.
    """
    key = _cache_key(profile.pk, feature)
    ttl = _seconds_until_midnight_utc()

    try:
        cache.incr(key)
    except ValueError:
        cache.set(key, 1, timeout=ttl)


def get_usage(profile_id: int) -> dict:
    """Return {feature: count} for all features for today."""
    return {feature: cache.get(_cache_key(profile_id, feature), 0) for feature in ALL_FEATURES}
