"""Run an AI feature on behalf of a profile: the one place quota is charged and refunded.

Interface (the test surface):
    * ``run_ai_feature(request, feature, work, ...)`` - what an endpoint calls. Checks the
      rate limit, reserves quota against ``request.auth``, resolves the owned recipe (404 if
      it is not that profile's), runs ``work`` and returns the response body or a ``Status``.
    * ``run_charged(profile, feature, work, ...)`` - the reserve/run/refund core, for callers
      (discover) that do their own pre-checks.
    * ``Ran(value, called_ai)`` - what ``work`` returns; ``called_ai=False`` (a cache hit)
      refunds the reservation.
    * ``AIFeatureError(status, error, message)`` - raise from ``work`` for an expected failure;
      the reservation is refunded and the error becomes that response.

Any other exception refunds the reservation and propagates (``handle_ai_errors`` on the
endpoint maps it). Quota is charged to the *same* profile that ownership is checked against.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from ninja import Status

from apps.recipes.models import Recipe

from .quota import release_quota, reserve_quota

security_logger = logging.getLogger("security")


@dataclass
class Ran:
    """Result of ``work``: ``called_ai`` is False when it was served from a cache."""

    value: Any
    called_ai: bool = True


class AIFeatureError(Exception):
    """An expected failure inside ``work``; becomes a ``Status`` response and refunds quota."""

    def __init__(self, status: int, error: str, message: str):
        super().__init__(message)
        self.status = status
        self.error = error
        self.message = message

    def response(self) -> Status:
        return Status(self.status, {"error": self.error, "message": self.message})


@dataclass
class FeatureContext:
    """What ``work`` receives: the acting profile and, when requested, its owned recipe."""

    profile: Any
    recipe: Recipe | None = None


def rate_limited_response(request) -> Status | None:
    """Return the 429 for a request django-ratelimit flagged as limited, else None."""
    if not getattr(request, "limited", False):
        return None
    security_logger.warning("Rate limit hit: %s from %s", request.path, request.META.get("REMOTE_ADDR"))
    return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})


def quota_exceeded_response(feature: str, info: dict) -> Status:
    return Status(429, {"error": "quota_exceeded", "message": f"Daily limit reached for {feature}", **info})


def run_charged(
    profile,
    feature: str,
    work: Callable[[], Ran],
    *,
    charge: bool = True,
    fallback: Callable[[], Any] | None = None,
):
    """Reserve quota for ``profile``, run ``work`` and refund when no AI call was made.

    ``charge=False`` skips reserving (and so refunding). ``fallback`` is consulted when the
    quota is exhausted: a non-None return is served instead of the 429.
    """
    if charge:
        allowed, info = reserve_quota(profile, feature)
        if not allowed:
            cached = fallback() if fallback is not None else None
            return cached if cached is not None else quota_exceeded_response(feature, info)

    try:
        outcome = work()
    except AIFeatureError as exc:
        if charge:
            release_quota(profile, feature)
        return exc.response()
    except Exception:
        if charge:
            release_quota(profile, feature)
        raise

    if charge and not outcome.called_ai:
        release_quota(profile, feature)
    return outcome.value


def _owned_recipe(profile, recipe_id: int, claimed_profile_id: int | None) -> Recipe:
    if claimed_profile_id is not None and claimed_profile_id != profile.id:
        raise AIFeatureError(404, "not_found", f"Profile {claimed_profile_id} not found")
    recipe = Recipe.objects.filter(id=recipe_id, profile_id=profile.id).first()
    if recipe is None:
        raise AIFeatureError(404, "not_found", f"Recipe {recipe_id} not found")
    return recipe


def run_ai_feature(
    request,
    feature: str,
    work: Callable[[FeatureContext], Ran],
    *,
    recipe_id: int | None = None,
    claimed_profile_id: int | None = None,
):
    """Run ``work`` as an AI feature for the authenticated profile (``request.auth``).

    ``recipe_id`` makes the recipe load (owned by that profile, else 404) part of the run, so a
    404 refunds the reservation. ``claimed_profile_id`` is a profile id the client sent in the
    body; it must equal the authenticated profile or the call is a 404.
    """
    limited = rate_limited_response(request)
    if limited is not None:
        return limited

    profile = request.auth

    def guarded() -> Ran:
        recipe = _owned_recipe(profile, recipe_id, claimed_profile_id) if recipe_id is not None else None
        return work(FeatureContext(profile=profile, recipe=recipe))

    return run_charged(profile, feature, guarded)
