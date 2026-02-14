"""Profile utilities."""

from asgiref.sync import sync_to_async
from django.http import Http404

from .models import Profile


def _get_deployment_mode():
    """Get the current deployment mode."""
    from apps.core.models import AppSettings

    return AppSettings.get().get_deployment_mode()


def get_current_profile(request):
    """
    Get the current profile based on deployment mode.

    Home mode: Uses session['profile_id']
    Public mode: Uses request.user.profile

    Raises Http404 if no profile is available.
    """
    deployment_mode = _get_deployment_mode()

    if deployment_mode == "public":
        # Public mode: use authenticated user's profile
        if not request.user.is_authenticated:
            raise Http404("Not authenticated")
        if not hasattr(request.user, "profile"):
            raise Http404("No profile for user")
        return request.user.profile

    # Home mode: use session
    profile_id = request.session.get("profile_id")
    if not profile_id:
        raise Http404("No profile selected")

    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        raise Http404("Profile not found")


def get_current_profile_or_none(request):
    """
    Get the current profile, or None if not available.

    Home mode: Uses session['profile_id']
    Public mode: Uses request.user.profile

    Use this for endpoints that work with or without a profile,
    but need to apply profile-based filtering when one is present.
    """
    deployment_mode = _get_deployment_mode()

    if deployment_mode == "public":
        # Public mode: use authenticated user's profile
        if not request.user.is_authenticated:
            return None
        if not hasattr(request.user, "profile"):
            return None
        return request.user.profile

    # Home mode: use session
    profile_id = request.session.get("profile_id")
    if not profile_id:
        return None

    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return None


async def aget_current_profile_or_none(request):
    """
    Async version of get_current_profile_or_none.

    Use this in async views/endpoints.
    """

    @sync_to_async
    def _get_profile():
        return get_current_profile_or_none(request)

    return await _get_profile()
