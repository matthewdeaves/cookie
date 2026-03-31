"""Tests for apps/profiles/utils.py — profile retrieval utilities."""

from unittest.mock import MagicMock

import pytest
from django.http import Http404

from apps.profiles.models import Profile
from apps.profiles.utils import (
    aget_current_profile_or_none,
    get_current_profile,
    get_current_profile_or_none,
)


def _make_request(profile_id=None):
    """Create a mock request with a session dict."""
    request = MagicMock()
    session = {}
    if profile_id is not None:
        session["profile_id"] = profile_id
    request.session = session
    return request


@pytest.mark.django_db
class TestGetCurrentProfile:
    """Tests for get_current_profile()."""

    def test_returns_profile_when_valid(self, db):
        """Returns the Profile when session has a valid profile_id."""
        profile = Profile.objects.create(name="Alice", avatar_color="#aabbcc")
        request = _make_request(profile_id=profile.id)
        result = get_current_profile(request)
        assert result.id == profile.id
        assert result.name == "Alice"

    def test_raises_404_when_no_profile_id_in_session(self):
        """Raises Http404 when session has no profile_id."""
        request = _make_request(profile_id=None)
        with pytest.raises(Http404, match="No profile selected"):
            get_current_profile(request)

    def test_raises_404_when_profile_does_not_exist(self, db):
        """Raises Http404 when profile_id refers to a nonexistent profile."""
        request = _make_request(profile_id=999999)
        with pytest.raises(Http404, match="Profile not found"):
            get_current_profile(request)


@pytest.mark.django_db
class TestGetCurrentProfileOrNone:
    """Tests for get_current_profile_or_none()."""

    def test_returns_profile_when_valid(self, db):
        """Returns the Profile when session has a valid profile_id."""
        profile = Profile.objects.create(name="Bob", avatar_color="#112233")
        request = _make_request(profile_id=profile.id)
        result = get_current_profile_or_none(request)
        assert result is not None
        assert result.id == profile.id

    def test_returns_none_when_no_profile_id(self):
        """Returns None when session has no profile_id."""
        request = _make_request(profile_id=None)
        result = get_current_profile_or_none(request)
        assert result is None

    def test_returns_none_when_profile_does_not_exist(self, db):
        """Returns None when profile_id refers to a nonexistent profile."""
        request = _make_request(profile_id=999999)
        result = get_current_profile_or_none(request)
        assert result is None


@pytest.mark.django_db(transaction=True)
@pytest.mark.asyncio
class TestAgetCurrentProfileOrNone:
    """Tests for aget_current_profile_or_none() (async)."""

    async def test_returns_profile_when_valid(self):
        """Returns the Profile when session has a valid profile_id."""
        profile = await Profile.objects.acreate(name="Charlie", avatar_color="#445566")
        request = _make_request(profile_id=profile.id)
        result = await aget_current_profile_or_none(request)
        assert result is not None
        assert result.id == profile.id

    async def test_returns_none_when_no_profile_id(self):
        """Returns None when session has no profile_id."""
        request = _make_request(profile_id=None)
        result = await aget_current_profile_or_none(request)
        assert result is None

    async def test_returns_none_when_profile_does_not_exist(self):
        """Returns None when profile_id refers to a nonexistent profile."""
        request = _make_request(profile_id=999999)
        result = await aget_current_profile_or_none(request)
        assert result is None
