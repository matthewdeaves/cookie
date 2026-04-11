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
from django.core.management.base import CommandError

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

    def test_create_user_regular(self, passkey_mode):
        """create-user creates a regular user with profile."""
        _, data = _call("create-user", "testuser", as_json=True)
        assert data["ok"] is True
        assert data["user"]["username"] == "testuser"
        assert data["user"]["is_admin"] is False
        user = User.objects.get(username="testuser")
        assert user.is_active is True
        assert user.is_staff is False
        assert not user.has_usable_password()
        assert hasattr(user, "profile")

    def test_create_user_admin(self, passkey_mode):
        """create-user --admin creates an admin user."""
        _, data = _call("create-user", "adminuser", "--admin", as_json=True)
        assert data["ok"] is True
        assert data["user"]["is_admin"] is True
        assert User.objects.get(username="adminuser").is_staff is True

    def test_create_user_duplicate_refused(self, passkey_mode):
        """create-user refuses to create a duplicate username."""
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-user", "alice", as_json=True)

    def test_delete_user(self, passkey_mode):
        """delete-user removes user and profile."""
        _make_user("alice")
        _, data = _call("delete-user", "alice", as_json=True)
        assert data["ok"] is True
        assert data["deleted_user"]["username"] == "alice"
        assert not User.objects.filter(username="alice").exists()

    def test_delete_user_nonexistent(self, passkey_mode):
        """delete-user on nonexistent user fails."""
        with pytest.raises(SystemExit):
            _call("delete-user", "nobody", as_json=True)

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


@pytest.mark.django_db
class TestCreateSession:
    """cookie_admin create-session creates a Django session for a user."""

    def test_create_session_basic(self, passkey_mode):
        user = _make_user("alice")
        _, data = _call("create-session", "alice", as_json=True)

        assert data["ok"] is True
        assert "session_key" in data
        assert len(data["session_key"]) > 0
        assert data["user"]["username"] == "alice"
        assert data["expires_in_seconds"] == 3600
        assert data["profile_id"] == user.profile.id

        # Verify session exists in DB with correct auth keys
        from django.contrib.sessions.models import Session

        session = Session.objects.get(pk=data["session_key"])
        decoded = session.get_decoded()
        assert str(decoded.get("_auth_user_id")) == str(user.pk)
        assert decoded.get("profile_id") == user.profile.id

    def test_create_session_custom_ttl(self, passkey_mode):
        _make_user("alice")
        _, data = _call("create-session", "alice", "--ttl", "120", as_json=True)

        assert data["ok"] is True
        assert data["expires_in_seconds"] == 120

    def test_create_session_inactive_user_refused(self, passkey_mode):
        _make_user("alice", is_active=False)
        with pytest.raises(SystemExit):
            _call("create-session", "alice", as_json=True)

    def test_create_session_nonexistent_user(self, passkey_mode):
        with pytest.raises(SystemExit):
            _call("create-session", "nobody", as_json=True)

    def test_create_session_ttl_too_short(self, passkey_mode):
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-session", "alice", "--ttl", "10", as_json=True)

    def test_create_session_ttl_too_long(self, passkey_mode):
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-session", "alice", "--ttl", "100000", as_json=True)


class TestCreateSuperuserBlocked:
    """Django's createsuperuser must be blocked."""

    def test_createsuperuser_raises_error(self):
        with pytest.raises(CommandError, match="createsuperuser is disabled"):
            call_command("createsuperuser")


# ---------------------------------------------------------------------------
# Factory reset (CLI-only in passkey mode)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestCookieAdminReset:
    """Tests for the cookie_admin reset subcommand."""

    def test_reset_json_requires_confirm_flag(self, passkey_mode):
        """reset --json without --confirm should fail."""
        with pytest.raises(SystemExit):
            _call("reset", as_json=True)

    def test_reset_json_with_confirm_deletes_data(self, passkey_mode):
        """reset --json --confirm should delete all data and return success."""
        from apps.recipes.models import Recipe, RecipeFavorite

        user = _make_user("alice", is_staff=True)
        recipe = Recipe.objects.create(
            profile=user.profile,
            title="Test Recipe",
            host="test.com",
            ingredients=["flour"],
            instructions=["mix"],
        )
        RecipeFavorite.objects.create(profile=user.profile, recipe=recipe)

        assert Recipe.objects.count() == 1
        assert RecipeFavorite.objects.count() == 1
        assert User.objects.count() >= 1

        out = StringIO()
        call_command("cookie_admin", "reset", "--json", "--confirm", stdout=out, stderr=StringIO())
        result = json.loads(out.getvalue())

        assert result["ok"] is True
        assert "actions_performed" in result
        assert Recipe.objects.count() == 0
        assert RecipeFavorite.objects.count() == 0
        assert User.objects.count() == 0  # passkey mode deletes users
        assert Profile.objects.count() == 0

    def test_reset_preserves_search_sources(self, passkey_mode):
        """reset should preserve SearchSource configurations."""
        from apps.recipes.models import SearchSource

        _make_user("admin", is_staff=True)
        source, _ = SearchSource.objects.get_or_create(
            host="test.example.com",
            defaults={
                "name": "Test",
                "search_url_template": "https://test.example.com/search?q={query}",
                "result_selector": ".recipe",
                "is_enabled": True,
                "consecutive_failures": 5,
                "needs_attention": True,
            },
        )

        out = StringIO()
        call_command("cookie_admin", "reset", "--json", "--confirm", stdout=out, stderr=StringIO())

        source.refresh_from_db()
        assert source.consecutive_failures == 0
        assert source.needs_attention is False

    def test_reset_clears_sessions(self, passkey_mode):
        """reset should clear all sessions."""
        from django.contrib.sessions.models import Session

        _make_user("admin", is_staff=True)

        # Create a session
        from django.contrib.sessions.backends.db import SessionStore
        s = SessionStore()
        s["test"] = "value"
        s.create()
        assert Session.objects.count() >= 1

        out = StringIO()
        call_command("cookie_admin", "reset", "--json", "--confirm", stdout=out, stderr=StringIO())

        assert Session.objects.count() == 0

    def test_reset_not_available_in_home_mode(self):
        """reset should fail in home mode (cookie_admin is passkey-only)."""
        with pytest.raises(SystemExit):
            _call("reset", as_json=True)
