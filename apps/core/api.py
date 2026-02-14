"""System API for administrative operations like database reset."""

import os
import shutil

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.sessions.models import Session
from ninja import Router, Schema

from apps.core.models import AppSettings
from apps.core.utils import is_admin
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

router = Router(tags=["system"])


class HealthSchema(Schema):
    status: str
    database: str


@router.get("/health/", response=HealthSchema)
def health_check(request):
    """Simple health check for container orchestration."""
    from django.db import connection

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return {"status": "healthy", "database": "ok"}
    except Exception:
        return {"status": "unhealthy", "database": "error"}


class ErrorSchema(Schema):
    error: str
    message: str


class EnvOverridesSchema(Schema):
    deployment_mode: bool
    allow_registration: bool
    instance_name: bool


class AuthSettingsSchema(Schema):
    deployment_mode: str
    allow_registration: bool
    instance_name: str
    is_admin: bool
    env_overrides: EnvOverridesSchema


class AuthSettingsUpdateSchema(Schema):
    deployment_mode: str | None = None
    allow_registration: bool | None = None
    instance_name: str | None = None


class AuthSettingsUpdateResponseSchema(Schema):
    success: bool
    deployment_mode: str
    allow_registration: bool
    instance_name: str
    env_overrides: EnvOverridesSchema
    warnings: list[str]


@router.get("/auth-settings/", response=AuthSettingsSchema)
def get_auth_settings(request):
    """Get authentication/deployment settings for frontend."""
    app_settings = AppSettings.get()

    return {
        "deployment_mode": app_settings.get_deployment_mode(),
        "allow_registration": app_settings.get_allow_registration(),
        "instance_name": app_settings.get_instance_name(),
        "is_admin": is_admin(request.user),
        "env_overrides": {
            "deployment_mode": bool(os.environ.get("COOKIE_DEPLOYMENT_MODE")),
            "allow_registration": bool(os.environ.get("COOKIE_ALLOW_REGISTRATION")),
            "instance_name": bool(os.environ.get("COOKIE_INSTANCE_NAME")),
        },
    }


@router.put(
    "/auth-settings/",
    response={200: AuthSettingsUpdateResponseSchema, 400: ErrorSchema, 403: ErrorSchema},
)
def update_auth_settings(request, data: AuthSettingsUpdateSchema):
    """Update authentication/deployment settings.

    Admin-only endpoint. In home mode, all users are admin.
    In public mode, only COOKIE_ADMIN_USERNAME is admin.
    """
    if not is_admin(request.user):
        return 403, {"error": "forbidden", "message": "Admin access required"}

    app_settings = AppSettings.get()
    warnings = []

    # Check if deployment_mode is env-controlled
    if data.deployment_mode is not None:
        if os.environ.get("COOKIE_DEPLOYMENT_MODE"):
            warnings.append("deployment_mode is controlled by environment variable and cannot be changed")
        elif data.deployment_mode in ("home", "public"):
            app_settings.deployment_mode = data.deployment_mode
        else:
            return 400, {
                "error": "invalid_deployment_mode",
                "message": "deployment_mode must be 'home' or 'public'",
            }

    # Check if allow_registration is env-controlled
    if data.allow_registration is not None:
        if os.environ.get("COOKIE_ALLOW_REGISTRATION"):
            warnings.append("allow_registration is controlled by environment variable and cannot be changed")
        else:
            app_settings.allow_registration = data.allow_registration

    # Check if instance_name is env-controlled
    if data.instance_name is not None:
        if os.environ.get("COOKIE_INSTANCE_NAME"):
            warnings.append("instance_name is controlled by environment variable and cannot be changed")
        else:
            # Validate instance name length
            if len(data.instance_name.strip()) == 0:
                return 400, {
                    "error": "invalid_instance_name",
                    "message": "instance_name cannot be empty",
                }
            if len(data.instance_name) > 100:
                return 400, {
                    "error": "invalid_instance_name",
                    "message": "instance_name cannot exceed 100 characters",
                }
            app_settings.instance_name = data.instance_name.strip()

    app_settings.save()

    return {
        "success": True,
        "deployment_mode": app_settings.get_deployment_mode(),
        "allow_registration": app_settings.get_allow_registration(),
        "instance_name": app_settings.get_instance_name(),
        "env_overrides": {
            "deployment_mode": bool(os.environ.get("COOKIE_DEPLOYMENT_MODE")),
            "allow_registration": bool(os.environ.get("COOKIE_ALLOW_REGISTRATION")),
            "instance_name": bool(os.environ.get("COOKIE_INSTANCE_NAME")),
        },
        "warnings": warnings,
    }


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


class ResetSuccessSchema(Schema):
    success: bool
    message: str
    actions_performed: list[str]


@router.get("/reset-preview/", response={200: ResetPreviewSchema, 403: ErrorSchema})
def get_reset_preview(request):
    """Get summary of data that will be deleted on reset.

    Admin-only endpoint.
    """
    if not is_admin(request.user):
        return 403, {"error": "forbidden", "message": "Admin access required"}

    return 200, {
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


@router.post("/reset/", response={200: ResetSuccessSchema, 400: ErrorSchema, 403: ErrorSchema})
def reset_database(request, data: ResetConfirmSchema):
    """
    Completely reset the database to factory state.

    Admin-only endpoint. Requires confirmation_text="RESET" to proceed.
    """
    if not is_admin(request.user):
        return 403, {"error": "forbidden", "message": "Admin access required"}

    if data.confirmation_text != "RESET":
        return 400, {
            "error": "invalid_confirmation",
            "message": "Type RESET to confirm",
        }

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
            pass  # Command may not exist yet

        try:
            call_command("seed_ai_prompts", verbosity=0)
        except Exception:
            pass  # Command may not exist yet

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
        return 400, {"error": "reset_failed", "message": str(e)}
