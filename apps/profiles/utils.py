"""Profile utilities."""

from django.http import Http404

from .models import Profile


def get_current_profile(request):
    """
    Get the current profile from the session.

    Raises Http404 if no profile is selected.
    """
    profile_id = request.session.get('profile_id')
    if not profile_id:
        raise Http404('No profile selected')

    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        raise Http404('Profile not found')


def get_current_profile_or_none(request):
    """
    Get the current profile from the session, or None if not set.

    Use this for endpoints that work with or without a profile,
    but need to apply profile-based filtering when one is present.
    """
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return None

    try:
        return Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return None
