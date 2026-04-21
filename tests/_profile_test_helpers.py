"""
Shared helpers for profile-API tests.

Split into its own module (not conftest.py) because these are plain helpers,
not pytest fixtures — conftest fixtures would require repeating the test
setup even for tests that already have their own client state. Consumed by
tests/test_profiles_api.py and tests/test_profiles_preferences_api.py.
"""

from django.contrib.auth.models import User

from apps.profiles.models import Profile


def create_user(username, is_staff=False):
    """Create a passkey-mode user with an attached Profile."""
    user = User.objects.create_user(
        username=username,
        password="!",
        email="",
        is_active=True,
        is_staff=is_staff,
    )
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def login(client, user):
    """Force-log a test client in as `user` and set profile_id in session."""
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()
