"""Admin CLI tool for managing Cookie in passkey mode.

All subcommands support --json for structured output, making this tool
suitable for automation via SSM, scripts, or AI assistants.

Usage:
    manage.py cookie_admin status [--json]
    manage.py cookie_admin audit [--lines N] [--json]
    manage.py cookie_admin list-users [--active-only] [--admins-only] [--json]
    manage.py cookie_admin promote <username> [--json]
    manage.py cookie_admin demote <username> [--json]
    manage.py cookie_admin activate <username> [--json]
    manage.py cookie_admin deactivate <username> [--json]
"""

import json
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Count


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
        return {
            "username": user.username,
            "user_id": user.pk,
            "passkeys": passkey_count,
            "is_admin": user.is_staff,
            "is_active": user.is_active,
            "date_joined": user.date_joined.strftime("%Y-%m-%d"),
        }

    def _handle_status(self, options):
        from django.db import connection
        from django.utils import timezone

        from apps.core.models import AppSettings, DeviceCode, WebAuthnCredential

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
            from django.core.management import call_command
            from io import StringIO

            out = StringIO()
            call_command("migrate", "--check", stdout=out, stderr=out)
            status["migrations"] = "up to date"
        except SystemExit:
            status["migrations"] = "pending"

        # Users
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(is_staff=True, is_active=True).count()
        status["users"] = {"total": total_users, "active": active_users, "admins": admin_users}

        # Passkeys
        status["passkeys"] = WebAuthnCredential.objects.count()

        # Device codes
        now = timezone.now()
        pending = DeviceCode.objects.filter(status="pending", expires_at__gt=now).count()
        expired = (
            DeviceCode.objects.filter(expires_at__lte=now).exclude(status__in=["authorized", "invalidated"]).count()
        )
        status["device_codes"] = {"pending": pending, "stale_expired": expired}

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
        from django.core.cache import cache

        from apps.core.management.commands.cleanup_device_codes import CLEANUP_CACHE_KEY as DC_KEY
        from apps.core.management.commands.cleanup_sessions import CLEANUP_CACHE_KEY as SESS_KEY
        from apps.recipes.management.commands.cleanup_search_images import CLEANUP_CACHE_KEY as IMG_KEY

        status["maintenance"] = {
            "device_code_cleanup": cache.get(DC_KEY) or "never run",
            "session_cleanup": cache.get(SESS_KEY) or "never run",
            "search_image_cleanup": cache.get(IMG_KEY) or "never run",
        }

        if options.get("as_json"):
            self.stdout.write(json.dumps({"ok": True, **status}, indent=2))
            return

        self.stdout.write(f"Auth mode:    {status['auth_mode']}")
        self.stdout.write(f"Database:     {status['database']}")
        self.stdout.write(f"Migrations:   {status['migrations']}")
        self.stdout.write(f"Users:        {active_users} active ({admin_users} admin) / {total_users} total")
        self.stdout.write(f"Passkeys:     {status['passkeys']}")
        self.stdout.write(f"Device codes: {pending} pending, {expired} stale")
        src = status["openrouter"]["source"]
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
