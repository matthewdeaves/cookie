"""Tests for cookie_admin management command (T106-T114)."""

import pytest
from django.contrib.auth.models import User
from django.core.management import call_command
from io import StringIO

from apps.profiles.models import Profile


def _create_user(username, is_staff=False, is_active=True):
    user = User.objects.create_user(
        username=username,
        password="TestPass123!",  # pragma: allowlist secret
        email="",
        is_active=is_active,
        is_staff=is_staff,
    )
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


@pytest.mark.django_db
class TestCookieAdmin:
    @pytest.fixture(autouse=True)
    def _passkey_mode(self, settings):
        settings.AUTH_MODE = "passkey"

    def test_list_users(self):
        """T106: list-users shows users."""
        _create_user("alice", is_staff=True)
        _create_user("bob")
        out = StringIO()
        call_command("cookie_admin", "list-users", stdout=out)
        output = out.getvalue()
        assert "alice" in output
        assert "bob" in output

    def test_promote(self):
        """T107: promote sets is_staff=True."""
        _create_user("alice")
        out = StringIO()
        call_command("cookie_admin", "promote", "alice", stdout=out)
        assert User.objects.get(username="alice").is_staff is True

    def test_demote(self):
        """T108: demote sets is_staff=False."""
        _create_user("alice", is_staff=True)
        _create_user("bob", is_staff=True)
        out = StringIO()
        call_command("cookie_admin", "demote", "alice", stdout=out)
        assert User.objects.get(username="alice").is_staff is False

    def test_demote_last_admin_refused(self):
        """T109: demote last admin is refused."""
        _create_user("alice", is_staff=True)
        with pytest.raises(SystemExit) as exc_info:
            call_command("cookie_admin", "demote", "alice", stderr=StringIO())
        assert exc_info.value.code == 1

    def test_deactivate_activate(self):
        """T111: deactivate/activate toggle is_active."""
        _create_user("alice")
        out = StringIO()
        call_command("cookie_admin", "deactivate", "alice", stdout=out)
        assert User.objects.get(username="alice").is_active is False
        call_command("cookie_admin", "activate", "alice", stdout=out)
        assert User.objects.get(username="alice").is_active is True


@pytest.mark.django_db
class TestCookieAdminHomeMode:
    @pytest.fixture(autouse=True)
    def _home_mode(self, settings):
        settings.AUTH_MODE = "home"

    def test_all_subcommands_exit_code_2(self):
        """T114: All subcommands in home mode exit with code 2."""
        for subcmd in ["list-users", "promote alice", "demote alice"]:
            args = subcmd.split()
            with pytest.raises(SystemExit) as exc_info:
                call_command("cookie_admin", *args, stderr=StringIO())
            assert exc_info.value.code == 2
