"""
Shared profile-deletion logic.

Extracted so the home-mode `DELETE /api/profiles/{id}/` endpoint
(apps/profiles/api.py) and the passkey-mode self-delete endpoint
(apps/core/auth_api.py — `DELETE /api/auth/me/`) can both produce the
same deletion preview and perform the same cascade + media cleanup.

In passkey mode, deleting the Profile's User also deletes the Profile
via Django's CASCADE on the OneToOne, so the call sequence is:
  preview(profile) → collect image paths → user.delete() → rm images
In home mode there's no User; profile.delete() handles everything.
Both paths live-test the same Recipe.image cleanup to avoid orphan files.
"""

import os
from typing import Any

from django.conf import settings

from apps.profiles.models import Profile


def get_deletion_preview(profile: Profile) -> dict[str, Any]:
    """Build the deletion-preview payload for a single Profile.

    Counts data that will be removed by cascading profile deletion. The
    return shape matches DeletionPreviewSchema in apps/profiles/api.py.
    """
    # Local imports: keeps this module light and avoids Django's circular
    # import dance when deletion.py is imported before apps are ready.
    from apps.ai.models import AIDiscoverySuggestion
    from apps.recipes.models import (
        Recipe,
        RecipeCollection,
        RecipeCollectionItem,
        RecipeFavorite,
        RecipeViewHistory,
        ServingAdjustment,
    )

    remixes = Recipe.objects.filter(is_remix=True, remix_profile=profile)
    favorites = RecipeFavorite.objects.filter(profile=profile)
    collections = RecipeCollection.objects.filter(profile=profile)
    collection_items = RecipeCollectionItem.objects.filter(collection__profile=profile)
    view_history = RecipeViewHistory.objects.filter(profile=profile)
    scaling_cache = ServingAdjustment.objects.filter(profile=profile)
    discover_cache = AIDiscoverySuggestion.objects.filter(profile=profile)
    remix_images_count = remixes.exclude(image="").exclude(image__isnull=True).count()

    return {
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "avatar_color": profile.avatar_color,
            "created_at": profile.created_at,
        },
        "data_to_delete": {
            "remixes": remixes.count(),
            "remix_images": remix_images_count,
            "favorites": favorites.count(),
            "collections": collections.count(),
            "collection_items": collection_items.count(),
            "view_history": view_history.count(),
            "scaling_cache": scaling_cache.count(),
            "discover_cache": discover_cache.count(),
        },
        "warnings": [
            "All remixed recipes will be permanently deleted",
            "Recipe images for remixes will be removed from storage",
            "This action cannot be undone",
        ],
    }


def collect_remix_image_paths(profile: Profile) -> list[str]:
    """Snapshot remix image paths BEFORE the cascade delete.

    The Recipe rows vanish when the profile is deleted, so the file paths
    must be captured first to enable post-delete cleanup on disk.
    """
    from apps.recipes.models import Recipe

    return list(
        Recipe.objects.filter(is_remix=True, remix_profile=profile, image__isnull=False)
        .exclude(image="")
        .values_list("image", flat=True)
    )


def remove_remix_image_files(image_paths: list[str]) -> None:
    """Best-effort filesystem cleanup of remix image files.

    Called AFTER the DB cascade. We intentionally swallow OSError so that
    a missing or unwritable media file doesn't prevent account deletion
    from completing — the DB rows are already gone.
    """
    for image_path in image_paths:
        full_path = os.path.join(settings.MEDIA_ROOT, str(image_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            pass
