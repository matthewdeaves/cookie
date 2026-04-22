"""Template context processors for global template variables."""

from django.conf import settings


def app_context(request):
    """Provide auth_mode, version, and current profile theme to all templates."""
    profile = getattr(request, "profile", None)
    return {
        "auth_mode": settings.AUTH_MODE,
        "cookie_version": settings.COOKIE_VERSION,
        "current_profile_theme": profile.theme if profile else "light",
    }
