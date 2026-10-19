"""Factory reset: the single owner of "what gets wiped and how".

Interface (the test surface):
    * ``preview_counts()``  - row counts for everything ``reset_all`` would delete.
    * ``reset_all(...)``    - wipe user data, reset counters, clear media/cache/sessions, reseed.

Both are driven from ``RESET_TABLES`` so the preview can never drift from what is
actually deleted. The HTTP endpoint (home mode only) and the ``cookie_admin reset``
CLI are thin adapters over this module; the media root is injectable so tests never
touch the real ``MEDIA_ROOT``.
"""

from __future__ import annotations

import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.management import call_command

from apps.ai.models import AIDiscoverySuggestion
from apps.profiles.models import Profile
from apps.recipes.models import (
    CachedSearchImage,
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeFavorite,
    RecipeViewHistory,
    SearchSource,
    ServingAdjustment,
)

logger = logging.getLogger(__name__)

# (preview key, model) in FK-safe deletion order: leaf tables first.
RESET_TABLES = (
    ("ai_suggestions", AIDiscoverySuggestion),
    ("serving_adjustments", ServingAdjustment),
    ("view_history", RecipeViewHistory),
    ("collection_items", RecipeCollectionItem),
    ("collections", RecipeCollection),
    ("favorites", RecipeFavorite),
    ("cached_search_images", CachedSearchImage),
    ("recipes", Recipe),
    ("profiles", Profile),
)

MEDIA_SUBDIRS = ("recipe_images", "search_images")
SEED_COMMANDS = ("seed_search_sources", "seed_ai_prompts")


def preview_counts() -> dict[str, int]:
    """Row counts for every table ``reset_all`` deletes (plus recipes that have an image)."""
    counts = {key: model.objects.count() for key, model in RESET_TABLES}
    counts["recipe_images"] = Recipe.objects.exclude(image="").exclude(image__isnull=True).count()
    return counts


def delete_user_data() -> None:
    """Delete every table in ``RESET_TABLES`` in FK-safe order."""
    for _key, model in RESET_TABLES:
        model.objects.all().delete()


def delete_accounts() -> None:
    """Delete passkey accounts and device codes (passkey mode only; caller decides)."""
    from apps.core.models import DeviceCode

    DeviceCode.objects.all().delete()
    User.objects.all().delete()


def reset_source_counters() -> None:
    """Zero the health counters on search sources but keep their configuration."""
    SearchSource.objects.all().update(consecutive_failures=0, needs_attention=False, last_validated_at=None)


def clear_media(media_root: str | None = None, owner: tuple[int, int] | None = None) -> None:
    """Empty and recreate the recipe/search image directories under ``media_root``.

    ``owner`` is an optional ``(uid, gid)`` the recreated directories are chowned to
    (the CLI runs as root via ``docker exec`` but the app runs as an unprivileged user).
    """
    root = settings.MEDIA_ROOT if media_root is None else media_root
    for subdir in MEDIA_SUBDIRS:
        path = os.path.join(root, subdir)
        if os.path.exists(path):
            shutil.rmtree(path)
        os.makedirs(path, exist_ok=True)
        if owner is not None:
            os.chown(path, owner[0], owner[1])


def reseed() -> list[str]:
    """Re-run migrations and the optional seed commands. Returns the seeds that ran."""
    call_command("migrate", verbosity=0)
    seeded = []
    for cmd in SEED_COMMANDS:
        try:
            call_command(cmd, verbosity=0)
            seeded.append(cmd)
        except Exception as exc:
            # Seed commands are optional; log so operators can diagnose an empty reset.
            logger.debug("seed command %s skipped: %s", cmd, exc)
    return seeded


def reset_all(
    *,
    media_root: str | None = None,
    include_accounts: bool = False,
    media_owner: tuple[int, int] | None = None,
) -> list[str]:
    """Wipe the app back to factory state. Returns human-readable actions performed.

    ``include_accounts`` also deletes Django users and device codes (passkey mode,
    CLI only - the HTTP adapter never sets it).
    """
    actions = []
    delete_user_data()
    actions.extend(
        [
            "Deleted all profiles",
            "Deleted all recipes",
            "Cleared favorites, collections, view history",
            "Cleared AI suggestions and serving adjustments",
        ]
    )
    if include_accounts:
        delete_accounts()
        actions.append("Deleted all user accounts and device codes")

    reset_source_counters()
    actions.append("Reset search source counters")

    clear_media(media_root, media_owner)
    actions.append("Cleared recipe and search images")

    cache.clear()
    Session.objects.all().delete()
    actions.extend(["Cleared application cache", "Cleared all sessions"])

    seeded = reseed()
    actions.append("Re-ran migrations")
    actions.extend(f"Seeded {cmd.replace('seed_', '')}" for cmd in seeded)
    return actions
