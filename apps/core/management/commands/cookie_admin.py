"""Admin CLI tool for managing Cookie in passkey mode.

All subcommands support --json for structured output, making this tool
suitable for automation via SSM, scripts, or AI assistants.

Usage:
    manage.py cookie_admin status [--json]
    manage.py cookie_admin audit [--lines N] [--json]
    manage.py cookie_admin list-users [--active-only] [--admins-only] [--json]
    manage.py cookie_admin create-user <username> [--admin] [--json]
    manage.py cookie_admin delete-user <username> [--json]
    manage.py cookie_admin promote <username> [--json]
    manage.py cookie_admin demote <username> [--json]
    manage.py cookie_admin activate <username> [--json]
    manage.py cookie_admin deactivate <username> [--json]
    manage.py cookie_admin set-unlimited <username> [--json]
    manage.py cookie_admin remove-unlimited <username> [--json]
    manage.py cookie_admin usage [--username <name>] [--json]
    manage.py cookie_admin create-session <username> [--ttl N] [--json]
    manage.py cookie_admin reset [--json --confirm]
"""

import json
import logging
import os
import shutil

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Count

security_logger = logging.getLogger("security")


class Command(BaseCommand):
    help = "Manage Cookie app and user accounts (passkey mode only). All subcommands support --json."

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
        ls.add_argument("--admins-only", action="store_true")
        ls.add_argument("--json", action="store_true", dest="as_json")

        # create-user
        cu = sub.add_parser("create-user", help="Create a headless user (no passkey)")
        cu.add_argument("username")
        cu.add_argument("--admin", action="store_true", help="Grant admin privileges")
        cu.add_argument("--json", action="store_true", dest="as_json")

        # delete-user
        du = sub.add_parser("delete-user", help="Delete a user and their profile")
        du.add_argument("username")
        du.add_argument("--json", action="store_true", dest="as_json")

        # promote
        p = sub.add_parser("promote", help="Grant admin privileges")
        p.add_argument("username")
        p.add_argument("--json", action="store_true", dest="as_json")

        # demote
        d = sub.add_parser("demote", help="Revoke admin privileges")
        d.add_argument("username")
        d.add_argument("--json", action="store_true", dest="as_json")

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
        su.add_argument("username")
        su.add_argument("--json", action="store_true", dest="as_json")

        # remove-unlimited
        ru = sub.add_parser("remove-unlimited", help="Revoke unlimited AI access")
        ru.add_argument("username")
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

        # reset
        rs = sub.add_parser("reset", help="Factory reset: delete all data and re-seed defaults")
        rs.add_argument("--confirm", action="store_true", help="Skip interactive prompt (required with --json)")
        rs.add_argument("--json", action="store_true", dest="as_json")

    def handle(self, *args, **options):
        if settings.AUTH_MODE != "passkey":
            self._error("cookie_admin is only available in passkey mode (AUTH_MODE=passkey).", options, code=2)

        subcommand = options.get("subcommand")
        if not subcommand:
            self._error("No subcommand provided. Use --help for usage.", options, code=1)

        handler = getattr(self, f"_handle_{subcommand.replace('-', '_')}", None)
        if handler:
            handler(options)
        else:
            self._error(f"Unknown subcommand '{subcommand}'", options, code=1)

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
            "is_admin": user.is_staff,
            "is_active": user.is_active,
            "unlimited_ai": unlimited_ai,
            "date_joined": user.date_joined.strftime("%Y-%m-%d"),
        }

    def _handle_status(self, options):
        status = self._collect_status()

        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, **status}, indent=2))
            return

        self._print_status(status)

    def _collect_status(self):
        from django.core.cache import cache
        from django.db import connection
        from django.utils import timezone

        from apps.core.management.commands.cleanup_device_codes import CLEANUP_CACHE_KEY as DC_KEY
        from apps.core.management.commands.cleanup_sessions import CLEANUP_CACHE_KEY as SESS_KEY
        from apps.core.models import AppSettings, DeviceCode, WebAuthnCredential
        from apps.recipes.management.commands.cleanup_search_images import CLEANUP_CACHE_KEY as IMG_KEY

        status = {"auth_mode": settings.AUTH_MODE}

        # Database
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            status["database"] = "ok"
        except Exception as e:
            status["database"] = f"error: {e}"

        # Migrations
        try:
            from io import StringIO

            from django.core.management import call_command

            out = StringIO()
            call_command("migrate", "--check", stdout=out, stderr=out)
            status["migrations"] = "up to date"
        except SystemExit:
            status["migrations"] = "pending"

        # Users
        status["users"] = {
            "total": User.objects.count(),
            "active": User.objects.filter(is_active=True).count(),
            "admins": User.objects.filter(is_staff=True, is_active=True).count(),
        }

        # Passkeys
        status["passkeys"] = WebAuthnCredential.objects.count()

        # Device codes
        now = timezone.now()
        status["device_codes"] = {
            "pending": DeviceCode.objects.filter(status="pending", expires_at__gt=now).count(),
            "stale_expired": DeviceCode.objects.filter(expires_at__lte=now)
            .exclude(status__in=["authorized", "invalidated"])
            .count(),
        }

        # AI / OpenRouter
        app_settings = AppSettings.get()
        has_env_key = bool(os.environ.get("OPENROUTER_API_KEY", ""))
        has_db_key = bool(app_settings._openrouter_api_key)
        status["openrouter"] = {
            "configured": bool(app_settings.openrouter_api_key),
            "source": "env" if has_env_key else ("database" if has_db_key else "none"),
            "model": app_settings.default_ai_model,
        }

        # WebAuthn config
        status["webauthn"] = {
            "rp_id": settings.WEBAUTHN_RP_ID or "(from request)",
            "rp_name": settings.WEBAUTHN_RP_NAME,
        }

        # Maintenance — last cleanup runs
        status["maintenance"] = {
            "device_code_cleanup": cache.get(DC_KEY) or "never run",
            "session_cleanup": cache.get(SESS_KEY) or "never run",
            "search_image_cleanup": cache.get(IMG_KEY) or "never run",
        }

        return status

    def _print_status(self, status):
        users = status["users"]
        dc = status["device_codes"]
        src = status["openrouter"]["source"]

        self.stdout.write(f"Auth mode:    {status['auth_mode']}")
        self.stdout.write(f"Database:     {status['database']}")
        self.stdout.write(f"Migrations:   {status['migrations']}")
        self.stdout.write(f"Users:        {users['active']} active ({users['admins']} admin) / {users['total']} total")
        self.stdout.write(f"Passkeys:     {status['passkeys']}")
        self.stdout.write(f"Device codes: {dc['pending']} pending, {dc['stale_expired']} stale")
        self.stdout.write(
            f"OpenRouter:   {'configured' if status['openrouter']['configured'] else 'not configured'} (source: {src})"
        )
        self.stdout.write(f"WebAuthn RP:  {status['webauthn']['rp_id']} ({status['webauthn']['rp_name']})")
        self.stdout.write("Maintenance:")
        for label, key in [
            ("  Device codes", "device_code_cleanup"),
            ("  Sessions", "session_cleanup"),
            ("  Search images", "search_image_cleanup"),
        ]:
            info = status["maintenance"][key]
            if isinstance(info, dict):
                self.stdout.write(
                    f"{label}: last ran {info['time'][:19]}, deleted {info['deleted']}, {info['remaining']} remaining"
                )
            else:
                self.stdout.write(f"{label}: {info}")

    def _handle_audit(self, options):
        max_lines = options.get("lines", 50)

        from django.utils import timezone

        now = timezone.now()
        since = now - timezone.timedelta(hours=24)

        events = (
            self._collect_registration_events(since, max_lines)
            + self._collect_login_events(since, max_lines)
            + self._collect_device_code_events(since, max_lines)
        )
        events.sort(key=lambda e: e["time"], reverse=True)
        events = events[:max_lines]

        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, "since": since.isoformat(), "events": events}, indent=2))
            return

        self.stdout.write(f"Security events (last 24h, max {max_lines}):")
        self.stdout.write("-" * 70)
        if not events:
            self.stdout.write("No events found.")
            return
        for e in events:
            self.stdout.write(self._format_audit_event(e))

    def _collect_registration_events(self, since, max_lines):
        """Collect user registration events since the given time."""
        recent_users = User.objects.filter(date_joined__gte=since).order_by("-date_joined")[:max_lines]
        return [
            {
                "time": u.date_joined.isoformat(),
                "type": "registration",
                "username": u.username,
                "is_admin": u.is_staff,
            }
            for u in recent_users
        ]

    def _collect_login_events(self, since, max_lines):
        """Collect passkey login events since the given time."""
        from apps.core.models import WebAuthnCredential

        recent_logins = (
            WebAuthnCredential.objects.filter(last_used_at__gte=since)
            .select_related("user")
            .order_by("-last_used_at")[:max_lines]
        )
        return [
            {
                "time": c.last_used_at.isoformat(),
                "type": "passkey_login",
                "username": c.user.username,
                "credential_id": c.pk,
            }
            for c in recent_logins
        ]

    def _collect_device_code_events(self, since, max_lines):
        """Collect device code events since the given time."""
        from apps.core.models import DeviceCode

        recent_codes = DeviceCode.objects.filter(created_at__gte=since).order_by("-created_at")[:max_lines]
        return [
            {
                "time": dc.created_at.isoformat(),
                "type": f"device_code_{dc.status}",
                "code": dc.code,
                "authorizer": dc.authorizing_user.username if dc.authorizing_user else None,
            }
            for dc in recent_codes
        ]

    @staticmethod
    def _format_audit_event(event):
        """Format a single audit event as a human-readable line."""
        ts = event["time"][:19].replace("T", " ")
        etype = event["type"]
        detail = event.get("username") or event.get("code") or ""
        extra = ""
        if etype == "passkey_login":
            extra = f" (credential #{event['credential_id']})"
        elif etype.startswith("device_code_") and event.get("authorizer"):
            extra = f" (by {event['authorizer']})"
        return f"  {ts}  {etype:<25} {detail}{extra}"

    def _handle_list_users(self, options):
        users = User.objects.all().order_by("date_joined")
        if options.get("active_only"):
            users = users.filter(is_active=True)
        if options.get("admins_only"):
            users = users.filter(is_staff=True)

        users = users.annotate(passkey_count=Count("webauthn_credentials"))

        if options.get("as_json"):
            data = [
                {
                    "username": u.username,
                    "user_id": u.pk,
                    "passkeys": u.passkey_count,
                    "is_admin": u.is_staff,
                    "is_active": u.is_active,
                    "unlimited_ai": getattr(getattr(u, "profile", None), "unlimited_ai", False),
                    "date_joined": u.date_joined.strftime("%Y-%m-%d"),
                }
                for u in users
            ]
            self.stdout.write(json.dumps({"ok": True, "users": data}, indent=2))
            return

        self.stdout.write(f"{'USERNAME':<15} {'ID':<6} {'PASSKEYS':<10} {'ADMIN':<7} {'ACTIVE':<8} {'JOINED'}")
        self.stdout.write("-" * 65)
        for u in users:
            self.stdout.write(
                f"{u.username:<15} {u.pk:<6} {u.passkey_count:<10} "
                f"{'yes' if u.is_staff else 'no':<7} "
                f"{'yes' if u.is_active else 'no':<8} "
                f"{u.date_joined.strftime('%Y-%m-%d')}"
            )
        active = users.filter(is_active=True).count()
        admins = users.filter(is_staff=True).count()
        self.stdout.write(f"\nTotal: {users.count()} users ({active} active, {admins} admin)")

    def _handle_create_user(self, options):
        from apps.profiles.models import Profile

        username = options["username"]
        is_admin = options.get("admin", False)

        if User.objects.filter(username=username).exists():
            self._error(f"User '{username}' already exists.", options)

        user = User.objects.create_user(
            username=username,
            password=None,
            email="",
            is_active=True,
            is_staff=is_admin,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        profile_count = Profile.objects.count()
        Profile.objects.create(
            user=user,
            name=f"User {profile_count + 1}",
            avatar_color=Profile.next_avatar_color(),
        )

        role = "admin" if is_admin else "regular"
        self._success(
            f"Created {role} user '{username}'.",
            options,
            {"user": self._user_dict(user)},
        )

    def _handle_delete_user(self, options):
        user = self._get_user(options["username"], options)
        username = user.username
        user_data = self._user_dict(user)
        user.delete()
        self._success(
            f"Deleted user '{username}' and associated data.",
            options,
            {"deleted_user": user_data},
        )

    def _handle_promote(self, options):
        user = self._get_user(options["username"], options)
        if user.is_staff:
            self._success(f"User '{user.username}' is already an admin.", options, {"user": self._user_dict(user)})
            return
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self._success(f"'{user.username}' is now an admin.", options, {"user": self._user_dict(user)})

    def _handle_demote(self, options):
        user = self._get_user(options["username"], options)
        if not user.is_staff:
            self._success(f"User '{user.username}' is not an admin.", options, {"user": self._user_dict(user)})
            return
        if User.objects.filter(is_staff=True).count() <= 1:
            self._error("Cannot demote the last remaining admin. Promote another user first.", options)
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        self._success(f"'{user.username}' is no longer an admin.", options, {"user": self._user_dict(user)})

    def _handle_activate(self, options):
        user = self._get_user(options["username"], options)
        user.is_active = True
        user.save(update_fields=["is_active"])
        self._success(f"'{user.username}' has been reactivated.", options, {"user": self._user_dict(user)})

    def _handle_deactivate(self, options):
        user = self._get_user(options["username"], options)
        user.is_active = False
        user.save(update_fields=["is_active"])
        from django.contrib.sessions.models import Session
        from django.utils import timezone

        count = 0
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if str(data.get("_auth_user_id")) == str(user.pk):
                session.delete()
                count += 1
        self._success(
            f"'{user.username}' has been deactivated and {count} session(s) invalidated.",
            options,
            {"user": self._user_dict(user), "sessions_invalidated": count},
        )

    def _handle_set_unlimited(self, options):
        user = self._get_user(options["username"], options)
        profile = user.profile
        profile.unlimited_ai = True
        profile.save(update_fields=["unlimited_ai"])
        self._success(
            f"Updated {user.username}: unlimited AI access granted",
            options,
            {"username": user.username, "user_id": user.pk, "unlimited_ai": True, "action": "set-unlimited"},
        )

    def _handle_remove_unlimited(self, options):
        user = self._get_user(options["username"], options)
        profile = user.profile
        profile.unlimited_ai = False
        profile.save(update_fields=["unlimited_ai"])
        self._success(
            f"Updated {user.username}: unlimited AI access revoked",
            options,
            {"username": user.username, "user_id": user.pk, "unlimited_ai": False, "action": "remove-unlimited"},
        )

    def _handle_usage(self, options):
        from datetime import date as date_cls

        from apps.ai.services.quota import ALL_FEATURES, FEATURE_LIMIT_FIELDS, get_usage
        from apps.core.models import AppSettings
        from apps.profiles.models import Profile

        app_settings = AppSettings.get()
        limits = {f: getattr(app_settings, FEATURE_LIMIT_FIELDS[f]) for f in ALL_FEATURES}
        today = date_cls.today().isoformat()
        users_data = self._collect_usage_data(options, get_usage, Profile)

        if options.get("as_json"):
            json_users = [
                {k: u[k] for k in ("username", "profile_name", "is_admin", "unlimited_ai", "usage")} for u in users_data
            ]
            self.stdout.write(json.dumps({"ok": True, "date": today, "users": json_users}, indent=2))
            return

        for u in users_data:
            self._print_user_usage(u, limits, ALL_FEATURES)

    def _collect_usage_data(self, options, get_usage, Profile):
        if options.get("username"):
            user = self._get_user(options["username"], options)
            profiles = [(user.profile, user)]
        else:
            profiles = [(p, p.user) for p in Profile.objects.select_related("user").filter(user__isnull=False)]
        return [
            {
                "username": user.username,
                "profile_name": profile.name,
                "is_admin": user.is_staff,
                "unlimited_ai": profile.unlimited_ai,
                "is_exempt": user.is_staff or profile.unlimited_ai,
                "usage": get_usage(profile.pk),
            }
            for profile, user in profiles
        ]

    def _print_user_usage(self, u, limits, all_features):
        tags = []
        if u["is_admin"]:
            tags.append("admin")
        if u["unlimited_ai"]:
            tags.append("unlimited")
        tag_str = f" [{'/'.join(tags)}]" if tags else ""
        self.stdout.write(f"{u['username']} ({u['profile_name']}){tag_str}")
        for feature in all_features:
            count = u["usage"][feature]
            suffix = "" if u["is_exempt"] else f"/{limits[feature]}"
            self.stdout.write(f"  {feature}: {count}{suffix}")
        self.stdout.write("")

    def _handle_create_session(self, options):
        import datetime
        import logging

        from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
        from django.contrib.sessions.backends.db import SessionStore
        from django.utils import timezone

        security_logger = logging.getLogger("security")

        user = self._get_user(options["username"], options)
        if not user.is_active:
            self._error(f"User '{user.username}' is inactive.", options)

        profile = getattr(user, "profile", None)
        if profile is None:
            self._error(f"User '{user.username}' has no profile.", options)

        ttl = options.get("ttl", 3600)
        if ttl < 60 or ttl > 86400:
            self._error("TTL must be between 60 and 86400 seconds.", options)

        # Create session with Django auth keys (same as django.contrib.auth.login())
        session = SessionStore()
        session[SESSION_KEY] = str(user.pk)
        session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
        session[HASH_SESSION_KEY] = user.get_session_auth_hash()
        session["profile_id"] = profile.id
        session.set_expiry(ttl)
        session.create()

        security_logger.info(
            "CLI session created: user_id=%s, username=%s, ttl=%ds",
            user.pk,
            user.username,
            ttl,
        )

        self._success(
            f"Session created for '{user.username}' (expires in {ttl}s).",
            options,
            {
                "session_key": session.session_key,
                "profile_id": profile.id,
                "user": self._user_dict(user),
                "expires_in_seconds": ttl,
                "expires_at": (timezone.now() + datetime.timedelta(seconds=ttl)).isoformat(),
            },
        )

    def _handle_reset(self, options):
        from django.contrib.sessions.models import Session
        from django.core.cache import cache
        from django.core.management import call_command

        from apps.ai.models import AIDiscoverySuggestion
        from apps.profiles.models import Profile
        from apps.recipes.models import (
            CachedSearchImage,
            Recipe,
            RecipeCollection,
            RecipeCollectionItem,
            RecipeFavorite,
            RecipeViewHistory,
            SearchSource,
            ServingAdjustment,
        )

        if options.get("as_json"):
            if not options.get("confirm"):
                self._error("--confirm flag required for non-interactive reset. Usage: cookie_admin reset --json --confirm", options)
        else:
            self.stderr.write("WARNING: This will permanently delete ALL data.")
            confirm = input("Type RESET to confirm: ")
            if confirm != "RESET":
                self._error("Aborted.", options)

        security_logger.warning("DATABASE RESET initiated via CLI (cookie_admin reset)")

        actions = []

        # Delete in FK-safe order
        AIDiscoverySuggestion.objects.all().delete()
        ServingAdjustment.objects.all().delete()
        RecipeViewHistory.objects.all().delete()
        RecipeCollectionItem.objects.all().delete()
        RecipeCollection.objects.all().delete()
        RecipeFavorite.objects.all().delete()
        CachedSearchImage.objects.all().delete()
        Recipe.objects.all().delete()
        Profile.objects.all().delete()
        actions.extend([
            "Deleted all profiles",
            "Deleted all recipes",
            "Cleared favorites, collections, view history",
            "Cleared AI suggestions and serving adjustments",
        ])

        if settings.AUTH_MODE == "passkey":
            from apps.core.models import DeviceCode

            DeviceCode.objects.all().delete()
            User.objects.all().delete()
            actions.append("Deleted all user accounts and device codes")

        SearchSource.objects.all().update(
            consecutive_failures=0,
            needs_attention=False,
            last_validated_at=None,
        )
        actions.append("Reset search source counters")

        # Clear media
        for subdir in ("recipe_images", "search_images"):
            path = os.path.join(settings.MEDIA_ROOT, subdir)
            if os.path.exists(path):
                shutil.rmtree(path)
                os.makedirs(path)
        actions.append("Cleared recipe and search images")

        cache.clear()
        Session.objects.all().delete()
        actions.extend(["Cleared application cache", "Cleared all sessions"])

        call_command("migrate", verbosity=0)
        actions.append("Re-ran migrations")

        for cmd in ("seed_search_sources", "seed_ai_prompts"):
            try:
                call_command(cmd, verbosity=0)
                actions.append(f"Seeded {cmd.replace('seed_', '')}")
            except Exception:
                pass

        security_logger.warning("DATABASE RESET completed successfully via CLI")

        self._success(
            "Database reset complete.",
            options,
            {"actions_performed": actions},
        )
