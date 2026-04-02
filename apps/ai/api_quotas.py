"""
AI quota management API endpoints.
"""

from ninja import Router, Schema, Status

from apps.core.auth import AdminAuth, SessionAuth
from apps.core.models import AppSettings

from .services.quota import get_usage, _next_midnight_utc_iso, ALL_FEATURES, FEATURE_LIMIT_FIELDS

router = Router(tags=["ai"])


# Schemas


class QuotaLimitsIn(Schema):
    remix: int
    remix_suggestions: int
    scale: int
    tips: int
    discover: int
    timer: int


class QuotaLimitsOut(Schema):
    remix: int
    remix_suggestions: int
    scale: int
    tips: int
    discover: int
    timer: int


class QuotaResponse(Schema):
    limits: QuotaLimitsOut
    usage: QuotaLimitsOut
    unlimited: bool
    resets_at: str


class ErrorOut(Schema):
    error: str
    message: str
    action: str | None = None


# Helpers


def _build_quota_response(profile, app_settings):
    """Build a QuotaResponse dict for the given profile."""
    limits = {feature: getattr(app_settings, FEATURE_LIMIT_FIELDS[feature]) for feature in ALL_FEATURES}
    usage = get_usage(profile.pk)
    unlimited = profile.unlimited_ai or (profile.user and profile.user.is_staff)
    return {
        "limits": limits,
        "usage": usage,
        "unlimited": unlimited,
        "resets_at": _next_midnight_utc_iso(),
    }


# Endpoints


@router.get("/quotas", response={200: QuotaResponse, 404: ErrorOut}, auth=SessionAuth())
def get_quotas(request):
    """Get current AI quota limits, usage, and reset time for the requesting user."""
    from django.conf import settings as django_settings

    if getattr(django_settings, "AUTH_MODE", "home") == "home":
        return Status(404, {"error": "not_found", "message": "Quotas are not available in home mode"})

    profile = request.auth
    app_settings = AppSettings.get()
    return _build_quota_response(profile, app_settings)


@router.put("/quotas", response={200: QuotaResponse, 404: ErrorOut}, auth=AdminAuth())
def update_quotas(request, data: QuotaLimitsIn):
    """Update AI quota limits (admin only)."""
    from django.conf import settings as django_settings

    if getattr(django_settings, "AUTH_MODE", "home") == "home":
        return Status(404, {"error": "not_found", "message": "Quotas are not available in home mode"})

    app_settings = AppSettings.get()
    for feature in ALL_FEATURES:
        setattr(app_settings, FEATURE_LIMIT_FIELDS[feature], getattr(data, feature))
    app_settings.save()

    profile = request.auth
    return _build_quota_response(profile, app_settings)
