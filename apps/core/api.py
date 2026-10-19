"""System API for administrative operations like database reset."""

import logging

from django.conf import settings
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from apps.core import factory_reset
from apps.core.auth import HomeOnlyAuth, SessionAuth

logger = logging.getLogger(__name__)
security_logger = logging.getLogger("security")

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


@router.get("/reset-preview/", response={200: ResetPreviewSchema}, auth=HomeOnlyAuth())
def get_reset_preview(request):
    """Get summary of data that will be deleted on reset. Home mode only — 404 in passkey mode."""
    return {
        "data_counts": factory_reset.preview_counts(),
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


@router.post("/reset/", response={200: ResetSuccessSchema, 400: ErrorSchema, 429: dict}, auth=HomeOnlyAuth())
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
        factory_reset.reset_all()

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
