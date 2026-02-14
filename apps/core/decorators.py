"""Core decorators for access control."""

from functools import wraps

from django.http import HttpResponseForbidden

from apps.core.utils import is_admin


def require_admin(view_func):
    """Decorator to restrict view to admin users only.

    Returns 403 Forbidden if user is not admin.
    In home mode, all users are considered admin.
    In public mode, only the COOKIE_ADMIN_USERNAME user is admin.

    Usage:
        @require_admin
        def settings_view(request):
            ...
    """

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_admin(request.user):
            return HttpResponseForbidden("Admin access required")
        return view_func(request, *args, **kwargs)

    return wrapper
