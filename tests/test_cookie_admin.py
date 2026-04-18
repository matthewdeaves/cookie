"""Tests for the cookie_admin management command (passkey mode CLI).

Covers core user management (list, activate, deactivate),
quota-related commands (set-unlimited, remove-unlimited, usage),
status/audit, JSON output, and home-mode rejection.

Admin privilege no longer exists (spec 014-remove-is-staff). promote/demote
subcommands and the --admin flag are gone; list-users/status/audit outputs
no longer carry admin/is_staff fields.
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
    """Tests for list-users, create-user, delete-user, activate, deactivate."""

    def test_list_users(self, passkey_mode):
        """list-users shows users."""
        _make_user("alice")
        _make_user("bob")
        text, _ = _call("list-users")
        assert "alice" in text
        assert "bob" in text

    def test_create_user(self, passkey_mode):
        """create-user creates a regular user with profile. All users are peers."""
        _, data = _call("create-user", "testuser", as_json=True)
        assert data["ok"] is True
        assert data["user"]["username"] == "testuser"
        assert "is_admin" not in data["user"], (
            "CLI output MUST NOT expose is_admin (spec 014-remove-is-staff, FR-014)"
        )
        user = User.objects.get(username="testuser")
        assert user.is_active is True
        assert user.is_staff is False, "Created users MUST have is_staff=False (FR-022)"
        assert not user.has_usable_password()
        assert hasattr(user, "profile")

    def test_create_user_rejects_admin_flag(self, passkey_mode):
        """--admin flag no longer exists on create-user (FR-013)."""
        # argparse treats unknown flags as errors
        with pytest.raises((SystemExit, CommandError)):
            call_command("cookie_admin", "create-user", "adminuser", "--admin", stderr=StringIO())

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

    def test_delete_last_user_succeeds(self, passkey_mode):
        """FR-015: delete-user on the sole remaining user MUST succeed (no admin floor)."""
        _make_user("onlyuser")
        _, data = _call("delete-user", "onlyuser", as_json=True)
        assert data["ok"] is True
        assert User.objects.count() == 0

    def test_delete_user_nonexistent(self, passkey_mode):
        """delete-user on nonexistent user fails."""
        with pytest.raises(SystemExit):
            _call("delete-user", "nobody", as_json=True)

    def test_promote_subcommand_removed(self, passkey_mode):
        """FR-012: the promote subcommand is gone."""
        with pytest.raises((SystemExit, CommandError)):
            call_command("cookie_admin", "promote", "alice", stderr=StringIO())

    def test_demote_subcommand_removed(self, passkey_mode):
        """FR-012: the demote subcommand is gone."""
        with pytest.raises((SystemExit, CommandError)):
            call_command("cookie_admin", "demote", "alice", stderr=StringIO())

    def test_list_users_admins_only_flag_removed(self, passkey_mode):
        """FR-014: --admins-only flag no longer exists on list-users."""
        with pytest.raises((SystemExit, CommandError)):
            call_command("cookie_admin", "list-users", "--admins-only", stderr=StringIO())

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
        _make_user("alice")
        _, data = _call("list-users", as_json=True)
        assert data["ok"] is True
        assert len(data["users"]) == 1
        assert data["users"][0]["username"] == "alice"
        assert "is_admin" not in data["users"][0], (
            "list-users JSON MUST NOT expose is_admin (FR-014)"
        )

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
            call_command("cookie_admin", "delete-user", "nonexistent", "--json", stdout=out)
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
        _make_user("alice")
        text, _ = _call("status")
        assert "Auth mode:" in text
        assert "passkey" in text
        assert "Database:" in text
        assert "admin" not in text.lower(), (
            "status text MUST NOT mention admins (FR-016a)"
        )

    def test_status_json(self, passkey_mode):
        _make_user("alice")
        _, data = _call("status", as_json=True)
        assert data["ok"] is True
        assert data["auth_mode"] == "passkey"
        assert data["database"] == "ok"
        assert data["users"]["total"] == 1
        assert data["users"]["active"] == 1
        assert "admins" not in data["users"], (
            "status --json MUST NOT expose admin counts (FR-016a)"
        )
        assert "active_admins" not in data["users"]
        assert "openrouter" in data
        assert "webauthn" in data

    def test_audit_empty(self, passkey_mode):
        _, data = _call("audit", as_json=True)
        assert data["ok"] is True
        assert data["events"] == []

    def test_audit_shows_recent_registration(self, passkey_mode):
        _make_user("alice")
        _, data = _call("audit", as_json=True)
        assert data["ok"] is True
        reg_events = [e for e in data["events"] if e["type"] == "registration"]
        assert len(reg_events) == 1
        assert reg_events[0]["username"] == "alice"
        assert "is_admin" not in reg_events[0], (
            "audit events MUST NOT expose is_admin (FR-016a)"
        )

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
        """User-lifecycle subcommands in home mode exit with code 2 (AUTH_MODE guard)."""
        for subcmd in ["list-users", "create-user alice", "delete-user alice"]:
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

    def test_set_unlimited_by_profile_id(self, passkey_mode):
        user = _make_user("diana")
        pid = str(user.profile.id)
        _, data = _call("set-unlimited", "--profile-id", pid, as_json=True)
        assert data["ok"] is True
        assert data["unlimited_ai"] is True
        user.profile.refresh_from_db()
        assert user.profile.unlimited_ai is True

    def test_remove_unlimited_by_profile_id(self, passkey_mode):
        user = _make_user("eve", unlimited_ai=True)
        pid = str(user.profile.id)
        _, data = _call("remove-unlimited", "--profile-id", pid, as_json=True)
        assert data["ok"] is True
        assert data["unlimited_ai"] is False
        user.profile.refresh_from_db()
        assert user.profile.unlimited_ai is False

    def test_set_unlimited_both_args_errors(self, passkey_mode):
        _make_user("frank")
        with pytest.raises(SystemExit):
            _call("set-unlimited", "frank", "--profile-id", "1", as_json=True)

    def test_set_unlimited_profile_id_not_found(self, passkey_mode):
        with pytest.raises(SystemExit):
            _call("set-unlimited", "--profile-id", "99999", as_json=True)


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
        _, data = _call("create-session", "alice", "--confirm", as_json=True)

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
        _, data = _call("create-session", "alice", "--ttl", "120", "--confirm", as_json=True)

        assert data["ok"] is True
        assert data["expires_in_seconds"] == 120

    def test_create_session_inactive_user_refused(self, passkey_mode):
        _make_user("alice", is_active=False)
        with pytest.raises(SystemExit):
            _call("create-session", "alice", "--confirm", as_json=True)

    def test_create_session_nonexistent_user(self, passkey_mode):
        with pytest.raises(SystemExit):
            _call("create-session", "nobody", "--confirm", as_json=True)

    def test_create_session_ttl_too_short(self, passkey_mode):
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-session", "alice", "--ttl", "10", "--confirm", as_json=True)

    def test_create_session_ttl_too_long(self, passkey_mode):
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-session", "alice", "--ttl", "100000", "--confirm", as_json=True)

    def test_create_session_json_without_confirm_errors(self, passkey_mode):
        _make_user("alice")
        with pytest.raises(SystemExit):
            _call("create-session", "alice", as_json=True)

    def test_create_session_json_with_confirm_succeeds(self, passkey_mode):
        _make_user("alice")
        _, data = _call("create-session", "alice", "--confirm", as_json=True)
        assert data["ok"] is True
        assert "session_key" in data


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

        user = _make_user("alice")
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

        _make_user("admin")
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

        _make_user("admin")

        # Create a session
        from django.contrib.sessions.backends.db import SessionStore
        s = SessionStore()
        s["test"] = "value"
        s.create()
        assert Session.objects.count() >= 1

        out = StringIO()
        call_command("cookie_admin", "reset", "--json", "--confirm", stdout=out, stderr=StringIO())

        assert Session.objects.count() == 0

    def test_reset_works_in_home_mode(self, settings):
        """reset is mode-agnostic after v1.42.0 — works in both modes."""
        settings.AUTH_MODE = "home"
        # Should NOT raise: reset is available in home mode now that cookie_admin's
        # blanket passkey-only guard was replaced by a per-subcommand allowlist.
        text, payload = _call("reset", "--confirm", as_json=True)
        assert payload["ok"] is True


# ---------------------------------------------------------------------------
# v1.42.0 — new subcommands (admin-surface lockdown feature)
# ---------------------------------------------------------------------------


@pytest.fixture
def home_mode(settings):
    settings.AUTH_MODE = "home"


@pytest.fixture
def security_log_capture(caplog):
    """Capture records from the `security` logger (which has propagate=False).

    The standard `caplog` fixture attaches to the root logger; our `security`
    logger doesn't propagate, so we attach caplog's handler directly to it.
    """
    import logging

    security = logging.getLogger("security")
    security.addHandler(caplog.handler)
    security.setLevel(logging.WARNING)
    try:
        yield caplog
    finally:
        security.removeHandler(caplog.handler)


@pytest.mark.django_db
class TestSetApiKey:
    def test_set_api_key_by_flag(self, security_log_capture, home_mode):
        from apps.core.models import AppSettings

        _call("set-api-key", "--key", "sk-test-1234")
        app = AppSettings.get()
        assert app.openrouter_api_key == "sk-test-1234"
        # Security log hit, but value NEVER in log record
        assert any("set-api-key" in r.getMessage() for r in security_log_capture.records)
        assert not any("sk-test-1234" in r.getMessage() for r in security_log_capture.records)

    def test_set_api_key_rejects_empty_key(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("set-api-key", "--key", "   ")
        assert exc_info.value.code == 2

    def test_set_api_key_rejects_empty_stdin(self, home_mode, monkeypatch):
        import io

        monkeypatch.setattr("sys.stdin", io.StringIO(""))
        with pytest.raises(SystemExit) as exc_info:
            call_command("cookie_admin", "set-api-key", "--stdin", stdout=StringIO(), stderr=StringIO())
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestSetDefaultModel:
    def test_set_default_model_valid(self, security_log_capture, home_mode):
        from apps.ai.models import AIPrompt
        from apps.core.models import AppSettings

        valid_model = AIPrompt.AVAILABLE_MODELS[0][0]
        _call("set-default-model", valid_model)
        app = AppSettings.get()
        assert app.default_ai_model == valid_model
        assert any("set-default-model" in r.getMessage() for r in security_log_capture.records)

    def test_set_default_model_invalid(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("set-default-model", "fake/does-not-exist")
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestPromptsSubcommands:
    def _make_prompt(self, prompt_type="recipe_remix"):
        from apps.ai.models import AIPrompt

        # Seeded prompts may already exist; update_or_create avoids unique-key conflicts.
        obj, _ = AIPrompt.objects.update_or_create(
            prompt_type=prompt_type,
            defaults={
                "name": "Test",
                "description": "test desc",
                "system_prompt": "system",
                "user_prompt_template": "user {x}",
                "model": "anthropic/claude-haiku-4.5",
                "is_active": True,
            },
        )
        return obj

    def test_prompts_list_json(self, home_mode):
        self._make_prompt("recipe_remix")
        self._make_prompt("tips_generation")
        text, payload = _call("prompts", "list", as_json=True)
        assert payload["ok"] is True
        types = {p["prompt_type"] for p in payload["prompts"]}
        assert {"recipe_remix", "tips_generation"} <= types

    def test_prompts_show_unknown(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("prompts", "show", "no-such-type")
        assert exc_info.value.code == 2

    def test_prompts_set_model_only(self, security_log_capture, home_mode):
        self._make_prompt("recipe_remix")
        from apps.ai.models import AIPrompt

        new_model = AIPrompt.AVAILABLE_MODELS[1][0]
        _call("prompts", "set", "recipe_remix", "--model", new_model)
        prompt = AIPrompt.objects.get(prompt_type="recipe_remix")
        assert prompt.model == new_model
        assert prompt.system_prompt == "system"  # unchanged
        assert any("prompts set" in r.getMessage() for r in security_log_capture.records)

    def test_prompts_set_requires_at_least_one_flag(self, home_mode):
        self._make_prompt("recipe_remix")
        with pytest.raises(SystemExit) as exc_info:
            _call("prompts", "set", "recipe_remix")
        assert exc_info.value.code == 2

    def test_prompts_set_missing_file(self, home_mode, tmp_path):
        self._make_prompt("recipe_remix")
        missing = tmp_path / "does-not-exist-xyz.txt"
        with pytest.raises(SystemExit) as exc_info:
            _call(
                "prompts",
                "set",
                "recipe_remix",
                "--system-file",
                str(missing),
            )
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestSourcesSubcommands:
    def _make_source(self, name="Example"):
        from apps.recipes.models import SearchSource

        # host is unique; use update_or_create to avoid conflicts with seeded sources.
        obj, _ = SearchSource.objects.update_or_create(
            host=f"{name.lower()}.example.com",
            defaults={
                "name": name,
                "search_url_template": f"https://{name.lower()}.example.com/search?q={{query}}",
                "result_selector": ".recipe-card",
                "is_enabled": True,
            },
        )
        return obj

    def test_sources_list_json(self, home_mode):
        self._make_source("Alpha")
        self._make_source("Beta")
        text, payload = _call("sources", "list", as_json=True)
        names = {s["name"] for s in payload["sources"]}
        assert {"Alpha", "Beta"} <= names

    def test_sources_toggle(self, security_log_capture, home_mode):
        source = self._make_source("Gamma")
        _call("sources", "toggle", str(source.id))
        source.refresh_from_db()
        assert source.is_enabled is False
        assert any("sources toggle" in r.getMessage() for r in security_log_capture.records)

    def test_sources_toggle_unknown(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("sources", "toggle", "99999")
        assert exc_info.value.code == 1

    def test_sources_toggle_all_disable(self, home_mode):
        self._make_source("Alpha")
        self._make_source("Beta")
        text, payload = _call("sources", "toggle-all", "--disable", as_json=True)
        assert payload["enabled"] is False
        assert payload["count"] >= 2

    def test_sources_set_selector(self, home_mode):
        source = self._make_source("Delta")
        _call("sources", "set-selector", str(source.id), "--selector", "article.recipe h1")
        source.refresh_from_db()
        assert source.result_selector == "article.recipe h1"

    def test_sources_set_selector_empty(self, home_mode):
        source = self._make_source("Echo")
        with pytest.raises(SystemExit) as exc_info:
            _call("sources", "set-selector", str(source.id), "--selector", "  ")
        assert exc_info.value.code == 2

    def test_sources_repair_requires_api_key(self, home_mode):
        """repair must fail cleanly with no DB write when no API key is configured."""
        from apps.core.models import AppSettings

        app = AppSettings.get()
        # Force-wipe the key by writing directly to the private field
        app._openrouter_api_key = ""
        app.save()
        source = self._make_source("Foxtrot")
        with pytest.raises(SystemExit) as exc_info:
            _call("sources", "repair", str(source.id))
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestQuotaSubcommands:
    def test_quota_show(self, home_mode):
        text, payload = _call("quota", "show", as_json=True)
        assert "remix" in payload["quotas"]
        assert all(isinstance(v, int) for v in payload["quotas"].values())

    def test_quota_set(self, security_log_capture, home_mode):
        from apps.core.models import AppSettings

        _call("quota", "set", "tips", "42")
        app = AppSettings.get()
        assert app.daily_limit_tips == 42
        assert any("quota set" in r.getMessage() for r in security_log_capture.records)

    def test_quota_set_negative_rejected(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("quota", "set", "tips", "-1")
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestRenameSubcommand:
    def test_rename_home_mode_by_profile_id(self, security_log_capture, home_mode):
        profile = Profile.objects.create(name="Old", avatar_color="#fff")
        _call("rename", str(profile.id), "--name", "New")
        profile.refresh_from_db()
        assert profile.name == "New"
        assert any("rename profile_id" in r.getMessage() for r in security_log_capture.records)

    def test_rename_home_mode_requires_profile_id(self, home_mode):
        with pytest.raises(SystemExit) as exc_info:
            _call("rename", "alice", "--name", "Bob")
        assert exc_info.value.code == 2  # home mode: positional must be integer

    def test_rename_passkey_by_username(self, security_log_capture, passkey_mode):
        user = _make_user("alice")
        _call("rename", "alice", "--name", "Alice Prime")
        user.profile.refresh_from_db()
        assert user.profile.name == "Alice Prime"

    def test_rename_empty_name(self, home_mode):
        profile = Profile.objects.create(name="X", avatar_color="#fff")
        with pytest.raises(SystemExit) as exc_info:
            _call("rename", str(profile.id), "--name", "   ")
        assert exc_info.value.code == 2


@pytest.mark.django_db
class TestStatusCacheBlock:
    def test_status_json_includes_cache(self, passkey_mode):
        text, payload = _call("status", as_json=True)
        assert "cache" in payload
        assert "cache_stats" in payload["cache"]


@pytest.mark.django_db
class TestModeAgnosticSubcommandsInHomeMode:
    """New subcommands work in home mode (no PASSKEY_ONLY guard)."""

    def test_quota_show_in_home(self, settings):
        settings.AUTH_MODE = "home"
        _call("quota", "show")

    def test_sources_list_in_home(self, settings):
        settings.AUTH_MODE = "home"
        _call("sources", "list")

    def test_set_default_model_in_home(self, settings):
        from apps.ai.models import AIPrompt

        settings.AUTH_MODE = "home"
        _call("set-default-model", AIPrompt.AVAILABLE_MODELS[0][0])
