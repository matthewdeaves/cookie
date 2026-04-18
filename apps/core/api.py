"""System API for administrative operations like database reset."""

import logging
import os
import shutil

from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.sessions.models import Session
from ninja import Router, Schema, Status

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeFavorite,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeViewHistory,
    SearchSource,
    ServingAdjustment,
    CachedSearchImage,
)
from apps.ai.models import AIDiscoverySuggestion, AIPrompt
from apps.core.auth import AdminAuth, HomeOnlyAdminAuth, SessionAuth

router = Router(tags=["system"])


class HealthSchema(Schema):
    status: str


class ReadySchema(Schema):
    status: str
    database: str


@router.get("/mode/", response={200: dict})
def get_mode(request):
    """Return the current operating mode. Also ensures CSRF cookie is set."""
    from django.middleware.csrf import get_token

    get_token(request)  # Forces Django to set the CSRF cookie
    # `version` was removed in v1.42.0 to eliminate deployment fingerprinting.
    # Operators check the version via `python manage.py cookie_admin status --json`.
    result = {"mode": settings.AUTH_MODE}
    if settings.AUTH_MODE == "passkey":
        result["registration_enabled"] = True
    return result


@router.get("/health/", response=HealthSchema)
def health_check(request):
    """Liveness probe — confirms the process is running. No dependency checks."""
    from django.middleware.csrf import get_token

    get_token(request)  # Ensures CSRF cookie is set for SPA
    return {"status": "healthy"}


@router.get("/ready/", response={200: ReadySchema, 503: ReadySchema})
def readiness_check(request):
    """Readiness probe — checks database connectivity."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Status(200, {"status": "ready", "database": "ok"})
    except Exception:
        return Status(503, {"status": "not_ready", "database": "error"})


class DataCountsSchema(Schema):
    profiles: int
    recipes: int
    recipe_images: int
    favorites: int
    collections: int
    collection_items: int
    view_history: int
    ai_suggestions: int
    serving_adjustments: int
    cached_search_images: int


class ResetPreviewSchema(Schema):
    data_counts: DataCountsSchema
    preserved: list[str]
    warnings: list[str]


class ResetConfirmSchema(Schema):
    confirmation_text: str  # Must be "RESET"


class ErrorSchema(Schema):
    error: str
    message: str


class ResetSuccessSchema(Schema):
    success: bool
    message: str
    actions_performed: list[str]


@router.get("/reset-preview/", response={200: ResetPreviewSchema}, auth=HomeOnlyAdminAuth())
def get_reset_preview(request):
    """Get summary of data that will be deleted on reset. Home mode only — 404 in passkey mode."""
    return {
        "data_counts": {
            "profiles": Profile.objects.count(),
            "recipes": Recipe.objects.count(),
            "recipe_images": Recipe.objects.exclude(image="").exclude(image__isnull=True).count(),
            "favorites": RecipeFavorite.objects.count(),
            "collections": RecipeCollection.objects.count(),
            "collection_items": RecipeCollectionItem.objects.count(),
            "view_history": RecipeViewHistory.objects.count(),
            "ai_suggestions": AIDiscoverySuggestion.objects.count(),
            "serving_adjustments": ServingAdjustment.objects.count(),
            "cached_search_images": CachedSearchImage.objects.count(),
        },
        "preserved": [
            "Search source configurations",
            "AI prompt templates",
            "Application settings",
        ],
        "warnings": [
            "All user data will be permanently deleted",
            "All recipe images will be removed from storage",
            "This action cannot be undone",
        ],
    }


@router.post("/reset/", response={200: ResetSuccessSchema, 400: ErrorSchema, 429: dict}, auth=HomeOnlyAdminAuth())
@ratelimit(key="ip", rate="1/h", method="POST", block=False)
def reset_database(request, data: ResetConfirmSchema):
    """
    Completely reset the database to factory state.

    Requires confirmation_text="RESET" to proceed.
    Rate limited to 1 request per hour per IP.
    Home mode only — 404 in passkey mode (use CLI: python manage.py cookie_admin reset).
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /system/reset/ from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})
    if data.confirmation_text != "RESET":
        return Status(
            400,
            {
                "error": "invalid_confirmation",
                "message": "Type RESET to confirm",
            },
        )

    client_ip = request.META.get("REMOTE_ADDR")
    user_info = getattr(request, "auth", None)
    security_logger.warning(
        "DATABASE RESET initiated by %s from %s",
        user_info,
        client_ip,
    )

    try:
        # 1. Clear database tables (order matters for FK constraints)
        # Start with leaf tables that depend on others
        AIDiscoverySuggestion.objects.all().delete()
        ServingAdjustment.objects.all().delete()
        RecipeViewHistory.objects.all().delete()
        RecipeCollectionItem.objects.all().delete()
        RecipeCollection.objects.all().delete()
        RecipeFavorite.objects.all().delete()
        CachedSearchImage.objects.all().delete()

        # Delete all recipes (this will cascade to related items)
        Recipe.objects.all().delete()

        # Delete all profiles
        Profile.objects.all().delete()

        # Reset SearchSource failure counters (keep selectors)
        SearchSource.objects.all().update(
            consecutive_failures=0,
            needs_attention=False,
            last_validated_at=None,
        )

        # 2. Clear recipe images
        images_dir = os.path.join(settings.MEDIA_ROOT, "recipe_images")
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            os.makedirs(images_dir)  # Recreate empty directory

        # Clear cached search images
        search_images_dir = os.path.join(settings.MEDIA_ROOT, "search_images")
        if os.path.exists(search_images_dir):
            shutil.rmtree(search_images_dir)
            os.makedirs(search_images_dir)  # Recreate empty directory

        # 3. Clear Django cache
        cache.clear()

        # 4. Clear all sessions
        Session.objects.all().delete()

        # 5. Re-run migrations (ensures clean state)
        call_command("migrate", verbosity=0)

        # 6. Re-seed default data
        try:
            call_command("seed_search_sources", verbosity=0)
        except Exception:
            logger.debug("seed_search_sources command not available, skipping")

        try:
            call_command("seed_ai_prompts", verbosity=0)
        except Exception:
            logger.debug("seed_ai_prompts command not available, skipping")

        security_logger.warning(
            "DATABASE RESET completed successfully by %s from %s",
            user_info,
            client_ip,
        )

        return {
            "success": True,
            "message": "Database reset complete",
            "actions_performed": [
                "Deleted all user profiles",
                "Deleted all recipes and images",
                "Cleared all favorites and collections",
                "Cleared all view history",
                "Cleared all AI cache data",
                "Cleared all cached search images",
                "Reset search source counters",
                "Cleared application cache",
                "Cleared all sessions",
                "Re-ran database migrations",
                "Restored default seed data",
            ],
        }

    except Exception as e:
        logger.error("Database reset failed: %s", str(e), exc_info=True)
        return Status(400, {"error": "reset_failed", "message": "Database reset failed. Check server logs."})
