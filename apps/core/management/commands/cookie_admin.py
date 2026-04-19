"""Admin CLI for Cookie. Covers user lifecycle (passkey mode) and app config (either mode).

All subcommands support --json for structured output.

Admin privilege does not exist in passkey mode — all passkey users are peers.
App configuration is reached exclusively via this CLI (spec 014-remove-is-staff).

Passkey-only (require AUTH_MODE=passkey — operate on Django User / DeviceCode):
    cookie_admin list-users [--active-only] [--json]
    cookie_admin create-user <username> [--json]
    cookie_admin delete-user <username> [--json]
    cookie_admin activate <username> [--json]
    cookie_admin deactivate <username> [--json]
    cookie_admin set-unlimited <username> [--json]
    cookie_admin remove-unlimited <username> [--json]
    cookie_admin usage [--username <name>] [--json]
    cookie_admin create-session <username> [--ttl N] [--json]

Mode-agnostic (operate on AppSettings / AIPrompt / SearchSource / Profile):
    cookie_admin status [--json]                       # adds a 'cache' block in --json
    cookie_admin audit [--lines N] [--json]
    cookie_admin reset [--json --confirm]
    cookie_admin set-api-key [--key KEY | --stdin]
    cookie_admin test-api-key [--key KEY | --stdin] [--json]
    cookie_admin set-default-model <model_id> [--json]
    cookie_admin prompts list [--json]
    cookie_admin prompts show <prompt_type> [--json]
    cookie_admin prompts set <prompt_type> [--system-file PATH] [--user-file PATH]
                                            [--model MODEL] [--active {true,false}] [--json]
    cookie_admin sources list [--attention] [--json]
    cookie_admin sources toggle <source_id> [--json]
    cookie_admin sources toggle-all {--enable | --disable} [--json]
    cookie_admin sources set-selector <source_id> --selector CSS [--json]
    cookie_admin sources test [--id N | --all] [--json]
    cookie_admin sources repair <source_id> [--json]
    cookie_admin quota show [--json]
    cookie_admin quota set {remix|remix-suggestions|scale|tips|discover|timer} <N> [--json]
    cookie_admin rename <user_or_profile> --name NEW [--json]

Implementation split across sibling `_cookie_admin_*.py` mixins to keep
each file under the 500-line quality gate. Django's management loader
ignores `_`-prefixed files so only this module registers as the command.
"""

import json
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from apps.core.management.commands._cookie_admin_app import AppConfigMixin
from apps.core.management.commands._cookie_admin_resources import ResourcesMixin
from apps.core.management.commands._cookie_admin_users import UsersStatusMixin

security_logger = logging.getLogger("security")


class Command(UsersStatusMixin, AppConfigMixin, ResourcesMixin, BaseCommand):
    help = "Manage Cookie app config, users, and data. User-lifecycle subcommands require passkey mode; others work in either mode. All subcommands support --json."

    # Subcommands that operate on Django User / DeviceCode require AUTH_MODE=passkey.
    # App-config subcommands (AppSettings / AIPrompt / SearchSource / Profile) work in either mode.
    PASSKEY_ONLY_SUBCOMMANDS = frozenset(
        {
            "list-users",
            "create-user",
            "delete-user",
            "activate",
            "deactivate",
            "set-unlimited",
            "remove-unlimited",
            "usage",
            "create-session",
        }
    )

    def add_arguments(self, parser):
        parser.add_argument("--json", action="store_true", dest="as_json", help="Output as JSON (all subcommands)")
        sub = parser.add_subparsers(dest="subcommand")

        # status
        st = sub.add_parser("status", help="App status overview (config, DB, users, AI)")
        st.add_argument("--json", action="store_true", dest="as_json")

        # audit
        au = sub.add_parser("audit", help="Recent security events")
        au.add_argument("--lines", type=int, default=50, help="Max events to show (default 50)")
        au.add_argument("--json", action="store_true", dest="as_json")

        # list-users
        ls = sub.add_parser("list-users", help="List all users")
        ls.add_argument("--active-only", action="store_true")
        ls.add_argument("--json", action="store_true", dest="as_json")

        # create-user
        cu = sub.add_parser("create-user", help="Create a headless user (no passkey)")
        cu.add_argument("username")
        cu.add_argument("--json", action="store_true", dest="as_json")

        # delete-user
        du = sub.add_parser("delete-user", help="Delete a user and their profile")
        du.add_argument("username")
        du.add_argument("--json", action="store_true", dest="as_json")

        # activate
        a = sub.add_parser("activate", help="Reactivate a user account")
        a.add_argument("username")
        a.add_argument("--json", action="store_true", dest="as_json")

        # deactivate
        da = sub.add_parser("deactivate", help="Deactivate a user account")
        da.add_argument("username")
        da.add_argument("--json", action="store_true", dest="as_json")

        # set-unlimited
        su = sub.add_parser("set-unlimited", help="Grant unlimited AI access")
        su.add_argument("username", nargs="?", default=None)
        su.add_argument("--profile-id", type=int, dest="profile_id")
        su.add_argument("--json", action="store_true", dest="as_json")

        # remove-unlimited
        ru = sub.add_parser("remove-unlimited", help="Revoke unlimited AI access")
        ru.add_argument("username", nargs="?", default=None)
        ru.add_argument("--profile-id", type=int, dest="profile_id")
        ru.add_argument("--json", action="store_true", dest="as_json")

        # usage
        us = sub.add_parser("usage", help="Show AI usage for today")
        us.add_argument("--username", required=False, help="Show usage for a specific user")
        us.add_argument("--json", action="store_true", dest="as_json")

        # create-session
        cs = sub.add_parser("create-session", help="Create a Django session for a user (pentest/automation)")
        cs.add_argument("username")
        cs.add_argument("--ttl", type=int, default=3600, help="Session TTL in seconds (default 3600)")
        cs.add_argument("--json", action="store_true", dest="as_json")
        cs.add_argument("--confirm", action="store_true", help="Required for non-interactive (--json) mode")

        # reset
        rs = sub.add_parser("reset", help="Factory reset: delete all data and re-seed defaults")
        rs.add_argument("--confirm", action="store_true", help="Skip interactive prompt (required with --json)")
        rs.add_argument("--json", action="store_true", dest="as_json")

        # set-api-key
        sak = sub.add_parser("set-api-key", help="Set the OpenRouter API key in AppSettings")
        sak_group = sak.add_mutually_exclusive_group(required=True)
        sak_group.add_argument("--key", help="API key (avoid in shared shells)")
        sak_group.add_argument("--stdin", action="store_true", help="Read key from standard input")
        sak.add_argument("--json", action="store_true", dest="as_json")

        # test-api-key
        tak = sub.add_parser("test-api-key", help="Validate an OpenRouter API key without saving")
        tak_group = tak.add_mutually_exclusive_group(required=True)
        tak_group.add_argument("--key")
        tak_group.add_argument("--stdin", action="store_true")
        tak.add_argument("--json", action="store_true", dest="as_json")

        # set-default-model
        sdm = sub.add_parser("set-default-model", help="Set the default AI model id in AppSettings")
        sdm.add_argument("model_id")
        sdm.add_argument("--json", action="store_true", dest="as_json")

        # prompts
        pr = sub.add_parser("prompts", help="AI prompt management")
        pr_sub = pr.add_subparsers(dest="prompts_action")
        pr_list = pr_sub.add_parser("list", help="List AI prompts")
        pr_list.add_argument("--json", action="store_true", dest="as_json")
        pr_show = pr_sub.add_parser("show", help="Show one AI prompt by type")
        pr_show.add_argument("prompt_type")
        pr_show.add_argument("--json", action="store_true", dest="as_json")
        pr_set = pr_sub.add_parser("set", help="Update an AI prompt's fields (file-based content)")
        pr_set.add_argument("prompt_type")
        pr_set.add_argument("--system-file", dest="system_file", help="Path to new system prompt (UTF-8)")
        pr_set.add_argument("--user-file", dest="user_file", help="Path to new user template (UTF-8)")
        pr_set.add_argument("--model", dest="model", help="Model id (must be in AIPrompt.AVAILABLE_MODELS)")
        pr_set.add_argument("--active", dest="active", choices=["true", "false"], help="Set is_active")
        pr_set.add_argument("--json", action="store_true", dest="as_json")

        # sources
        sr = sub.add_parser("sources", help="Search-source management")
        sr_sub = sr.add_subparsers(dest="sources_action")
        sr_list = sr_sub.add_parser("list", help="List search sources")
        sr_list.add_argument("--attention", action="store_true", help="Only sources flagged needs_attention")
        sr_list.add_argument("--json", action="store_true", dest="as_json")
        sr_tog = sr_sub.add_parser("toggle", help="Flip a source's enabled state")
        sr_tog.add_argument("source_id", type=int)
        sr_tog.add_argument("--json", action="store_true", dest="as_json")
        sr_tall = sr_sub.add_parser("toggle-all", help="Set every source's enabled state")
        sr_tall_group = sr_tall.add_mutually_exclusive_group(required=True)
        sr_tall_group.add_argument("--enable", action="store_true")
        sr_tall_group.add_argument("--disable", action="store_true")
        sr_tall.add_argument("--json", action="store_true", dest="as_json")
        sr_sel = sr_sub.add_parser("set-selector", help="Overwrite a source's CSS selector")
        sr_sel.add_argument("source_id", type=int)
        sr_sel.add_argument("--selector", required=True)
        sr_sel.add_argument("--json", action="store_true", dest="as_json")
        sr_test = sr_sub.add_parser("test", help="Run the health-check on one source or all")
        sr_test_group = sr_test.add_mutually_exclusive_group(required=True)
        sr_test_group.add_argument("--id", dest="source_id", type=int)
        sr_test_group.add_argument("--all", action="store_true", dest="test_all")
        sr_test.add_argument("--json", action="store_true", dest="as_json")
        sr_rep = sr_sub.add_parser("repair", help="AI-assisted selector regeneration (requires API key)")
        sr_rep.add_argument("source_id", type=int)
        sr_rep.add_argument("--json", action="store_true", dest="as_json")

        # quota
        qt = sub.add_parser("quota", help="AI daily quota limits")
        qt_sub = qt.add_subparsers(dest="quota_action")
        qt_show = qt_sub.add_parser("show", help="Show all six daily limits")
        qt_show.add_argument("--json", action="store_true", dest="as_json")
        qt_set = qt_sub.add_parser("set", help="Set one daily limit")
        qt_set.add_argument(
            "feature",
            choices=["remix", "remix-suggestions", "scale", "tips", "discover", "timer"],
        )
        qt_set.add_argument("value", type=int)
        qt_set.add_argument("--json", action="store_true", dest="as_json")

        # rename
        rn = sub.add_parser(
            "rename",
            help="Rename a profile (passkey: by user_id|username; home: by profile_id)",
        )
        rn.add_argument("target", help="User id/username (passkey) or Profile id (home)")
        rn.add_argument("--name", required=True, help="New profile name")
        rn.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        subcommand = options.get("subcommand")
        if not subcommand:
            self._error("No subcommand provided. Use --help for usage.", options, code=1)

        if subcommand in self.PASSKEY_ONLY_SUBCOMMANDS and settings.AUTH_MODE != "passkey":
            self._error(f"'{subcommand}' requires AUTH_MODE=passkey.", options, code=2)

        # Nested-subcommand dispatch (prompts/sources/quota have per-action handlers).
        NESTED = {"prompts": "prompts_action", "sources": "sources_action", "quota": "quota_action"}
        if subcommand in NESTED:
            action = options.get(NESTED[subcommand])
            if not action:
                self._error(f"'{subcommand}' requires an action (see --help).", options, code=1)
            handler_name = f"_handle_{subcommand}_{action.replace('-', '_')}"
        else:
            handler_name = f"_handle_{subcommand.replace('-', '_')}"

        handler = getattr(self, handler_name, None)
        if handler:
            handler(options)
        else:
            self._error(f"Unknown subcommand '{subcommand}'", options, code=1)

    # ------------------------------------------------------------------ #
    # Shared helpers (used by every mixin's _handle_* methods)            #
    # ------------------------------------------------------------------ #

    def _error(self, message, options=None, code=1):
        if options and options.get("as_json"):
            self.stdout.write(json.dumps({"ok": False, "error": message}))
        else:
            self.stderr.write(f"Error: {message}")
        raise SystemExit(code)

    def _success(self, message, options, extra=None):
        if options.get("as_json"):
            result = {"ok": True, "message": message}
            if extra:
                result.update(extra)
            self.stdout.write(json.dumps(result))
        else:
            self.stdout.write(message)

    def _get_user(self, username, options):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            self._error(f"User '{username}' not found.", options)

    def _user_dict(self, user):
        passkey_count = user.webauthn_credentials.count()
        unlimited_ai = getattr(getattr(user, "profile", None), "unlimited_ai", False)
        return {
            "username": user.username,
            "user_id": user.pk,
            "passkeys": passkey_count,
            "is_active": user.is_active,
            "unlimited_ai": unlimited_ai,
            "date_joined": user.date_joined.strftime("%Y-%m-%d"),
        }
