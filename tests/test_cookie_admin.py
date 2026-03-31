"""Tests for the cookie_admin management command (passkey mode CLI).

Covers core user management (list, promote, demote, activate, deactivate),
quota-related commands (set-unlimited, remove-unlimited, usage),
status/audit, JSON output, and home-mode rejection.
"""

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


def _make_user(username, is_staff=False, is_active=True, unlimited_ai=False):
    """Create a User + Profile pair and return the user."""
    user = User.objects.create_user(username=username, password="!", email="", is_active=is_active, is_staff=is_staff)
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
# Core user management
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAdminUserManagement:
    """Tests for list-users, promote, demote, activate, deactivate."""

    def test_list_users(self, passkey_mode):
        """list-users shows users."""
        _make_user("alice", is_staff=True)
        _make_user("bob")
        text, _ = _call("list-users")
        assert "alice" in text
        assert "bob" in text

    def test_promote(self, passkey_mode):
        """promote sets is_staff=True."""
        _make_user("alice")
        _call("promote", "alice")
        assert User.objects.get(username="alice").is_staff is True

    def test_demote(self, passkey_mode):
        """demote sets is_staff=False."""
        _make_user("alice", is_staff=True)
        _make_user("bob", is_staff=True)
        _call("demote", "alice")
        assert User.objects.get(username="alice").is_staff is False

    def test_demote_last_admin_refused(self, passkey_mode):
        """demote last admin is refused."""
        _make_user("alice", is_staff=True)
        with pytest.raises(SystemExit) as exc_info:
            call_command("cookie_admin", "demote", "alice", stderr=StringIO())
        assert exc_info.value.code == 1

    def test_deactivate_activate(self, passkey_mode):
        """deactivate/activate toggle is_active."""
        _make_user("alice")
        _call("deactivate", "alice")
        assert User.objects.get(username="alice").is_active is False
        _call("activate", "alice")
        assert User.objects.get(username="alice").is_active is True


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAdminJsonOutput:
    """Tests for --json structured output on all subcommands."""

    def test_list_users_json(self, passkey_mode):
        _make_user("alice", is_staff=True)
        _, data = _call("list-users", as_json=True)
        assert data["ok"] is True
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "alice"
        assert data["users"][0]["is_admin"] is True

    def test_promote_json(self, passkey_mode):
        _make_user("alice")
        _, data = _call("promote", "alice", as_json=True)
        assert data["ok"] is True
        assert data["user"]["is_admin"] is True

    def test_demote_json(self, passkey_mode):
        _make_user("alice", is_staff=True)
        _make_user("bob", is_staff=True)
        _, data = _call("demote", "alice", as_json=True)
        assert data["ok"] is True
        assert data["user"]["is_admin"] is False

    def test_deactivate_json(self, passkey_mode):
        _make_user("alice")
        _, data = _call("deactivate", "alice", as_json=True)
        assert data["ok"] is True
        assert data["user"]["is_active"] is False
        assert "sessions_invalidated" in data

    def test_error_json(self, passkey_mode):
        """Errors with --json return structured error."""
        out = StringIO()
        with pytest.raises(SystemExit):
            call_command("cookie_admin", "promote", "nonexistent", "--json", stdout=out)
        data = json.loads(out.getvalue())
        assert data["ok"] is False
        assert "not found" in data["error"]


# ---------------------------------------------------------------------------
# Status and audit
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAdminStatusAudit:
    """Tests for status and audit subcommands."""

    def test_status_text(self, passkey_mode):
        _make_user("alice", is_staff=True)
        text, _ = _call("status")
        assert "Auth mode:" in text
        assert "passkey" in text
        assert "Database:" in text

    def test_status_json(self, passkey_mode):
        _make_user("alice", is_staff=True)
        _, data = _call("status", as_json=True)
        assert data["ok"] is True
        assert data["auth_mode"] == "passkey"
        assert data["database"] == "ok"
        assert data["users"]["admins"] == 1
        assert "openrouter" in data
        assert "webauthn" in data

    def test_audit_empty(self, passkey_mode):
        _, data = _call("audit", as_json=True)
        assert data["ok"] is True
        assert data["events"] == []

    def test_audit_shows_recent_registration(self, passkey_mode):
        _make_user("alice", is_staff=True)
        _, data = _call("audit", as_json=True)
        assert data["ok"] is True
        reg_events = [e for e in data["events"] if e["type"] == "registration"]
        assert len(reg_events) == 1
        assert reg_events[0]["username"] == "alice"

    def test_audit_text(self, passkey_mode):
        _make_user("alice")
        text, _ = _call("audit")
        assert "registration" in text
        assert "alice" in text

    def test_audit_respects_lines_limit(self, passkey_mode):
        for i in range(5):
            _make_user(f"user{i}")
        _, data = _call("audit", "--lines", "2", as_json=True)
        assert len(data["events"]) <= 2


# ---------------------------------------------------------------------------
# Home mode rejection
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAdminHomeMode:
    """All subcommands in home mode exit with code 2."""

    @pytest.fixture(autouse=True)
    def _home_mode(self, settings):
        settings.AUTH_MODE = "home"

    def test_all_subcommands_exit_code_2(self):
        for subcmd in ["list-users", "promote alice", "demote alice"]:
            args = subcmd.split()
            with pytest.raises(SystemExit) as exc_info:
                call_command("cookie_admin", *args, stderr=StringIO())
            assert exc_info.value.code == 2


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
