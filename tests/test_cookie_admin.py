"""Tests for the cookie_admin management command (passkey mode CLI)."""

import json
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command

from apps.profiles.models import Profile


@pytest.fixture(autouse=True)
def _clear_cache():
    """Ensure each test starts with an empty cache."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


def _make_user(username, is_staff=False, unlimited_ai=False):
    """Create a User + Profile pair and return the user."""
    user = User.objects.create_user(username=username, password="!", email="", is_active=True, is_staff=is_staff)
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850", unlimited_ai=unlimited_ai)
    return user


def _call(subcommand, *args, as_json=False):
    """Call cookie_admin and return (stdout_text, parsed_json_or_None)."""
    out = StringIO()
    cmd_args = [subcommand] + list(args)
    if as_json:
        cmd_args.append("--json")
    call_command("cookie_admin", *cmd_args, stdout=out, stderr=StringIO())
    text = out.getvalue()
    if as_json:
        return text, json.loads(text)
    return text, None


# ---------------------------------------------------------------------------
# set-unlimited / remove-unlimited
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSetUnlimitedCommand:
    """cookie_admin set-unlimited grants unlimited AI access."""

    def test_set_unlimited_command(self, passkey_mode):
        user = _make_user("alice")
        assert user.profile.unlimited_ai is False

        _call("set-unlimited", "alice")

        user.profile.refresh_from_db()
        assert user.profile.unlimited_ai is True

    def test_remove_unlimited_command(self, passkey_mode):
        user = _make_user("bob", unlimited_ai=True)
        assert user.profile.unlimited_ai is True

        _call("remove-unlimited", "bob")

        user.profile.refresh_from_db()
        assert user.profile.unlimited_ai is False

    def test_set_unlimited_json_output(self, passkey_mode):
        _make_user("charlie")
        _, data = _call("set-unlimited", "charlie", as_json=True)

        assert data["ok"] is True
        assert data["unlimited_ai"] is True
        assert data["username"] == "charlie"
        assert data["action"] == "set-unlimited"


# ---------------------------------------------------------------------------
# usage
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestUsageCommand:
    """cookie_admin usage shows per-user AI usage for today."""

    def test_usage_command_empty(self, passkey_mode):
        _make_user("alice")
        _make_user("bob")
        _, data = _call("usage", as_json=True)

        assert data["ok"] is True
        assert len(data["users"]) == 2
        for u in data["users"]:
            assert all(v == 0 for v in u["usage"].values())

    def test_usage_command_with_data(self, passkey_mode):
        from apps.ai.services.quota import increment_quota

        user = _make_user("alice")
        profile = user.profile

        increment_quota(profile, "remix")
        increment_quota(profile, "remix")
        increment_quota(profile, "tips")

        _, data = _call("usage", "--username", "alice", as_json=True)

        assert data["ok"] is True
        assert len(data["users"]) == 1
        usage = data["users"][0]["usage"]
        assert usage["remix"] == 2
        assert usage["tips"] == 1
        assert usage["scale"] == 0


# ---------------------------------------------------------------------------
# list-users shows unlimited_ai field
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestListUsersUnlimited:
    """cookie_admin list-users includes the unlimited_ai field."""

    def test_list_users_shows_unlimited_field(self, passkey_mode):
        _make_user("normal")
        _make_user("vip", unlimited_ai=True)

        _, data = _call("list-users", as_json=True)

        assert data["ok"] is True
        users_by_name = {u["username"]: u for u in data["users"]}
        assert users_by_name["normal"]["unlimited_ai"] is False
        assert users_by_name["vip"]["unlimited_ai"] is True
