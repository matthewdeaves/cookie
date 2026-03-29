"""Template context processors for global template variables."""

from django.conf import settings


def app_context(request):
    """Provide auth_mode and version to all templates."""
    return {
        "auth_mode": settings.AUTH_MODE,
        "cookie_version": settings.COOKIE_VERSION,
    }
