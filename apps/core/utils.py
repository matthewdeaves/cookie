"""Core utility functions."""

import os


def get_admin_username():
    """Get the admin username from environment variable.

    Returns:
        str: The admin username, or empty string if not configured.
    """
    return os.environ.get("COOKIE_ADMIN_USERNAME", "")


def is_admin(user):
    """Check if user has admin privileges.

    In home mode, everyone is effectively admin (no restrictions).
    In public mode, only the user matching COOKIE_ADMIN_USERNAME is admin.

    Args:
        user: Django User object (can be AnonymousUser)

    Returns:
        bool: True if user has admin privileges
    """
    from apps.core.models import AppSettings

    settings = AppSettings.get()

    # Home mode: everyone is effectively admin
    if settings.get_deployment_mode() == "home":
        return True

    # Public mode: check username against env var
    admin_username = get_admin_username()
    if not admin_username:
        # No admin configured = no admin access (secure default)
        return False

    return user.is_authenticated and user.username == admin_username
