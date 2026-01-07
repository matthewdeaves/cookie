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
