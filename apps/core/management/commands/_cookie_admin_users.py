"""User-lifecycle + status/audit handlers for `cookie_admin`.

Split out of `cookie_admin.py` to keep individual files under the 500-line
quality gate. Methods here assume `self` is a `Command` instance (see the
main module) so `self.stdout`, `self._error`, `self._success`, etc. are
always available.
"""

from __future__ import annotations

import json
import logging
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Count

security_logger = logging.getLogger("security")


class UsersStatusMixin:
    """Status/audit + user-lifecycle subcommand handlers."""

    # ------------------------------------------------------------------ #
    # status                                                              #
    # ------------------------------------------------------------------ #

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

        # Cache (image-cache health) — parity with the now-gated
        # GET /api/recipes/cache/health/ endpoint.
        try:
            from apps.recipes.api import get_cache_health_dict

            status["cache"] = get_cache_health_dict()
        except Exception as e:
            status["cache"] = {"status": f"error: {e}"}

        return status

    def _print_status(self, status):
        users = status["users"]
        dc = status["device_codes"]
        src = status["openrouter"]["source"]

        self.stdout.write(f"Auth mode:    {status['auth_mode']}")
        self.stdout.write(f"Database:     {status['database']}")
        self.stdout.write(f"Migrations:   {status['migrations']}")
        self.stdout.write(f"Users:        {users['active']} active / {users['total']} total")
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

    # ------------------------------------------------------------------ #
    # audit                                                               #
    # ------------------------------------------------------------------ #

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

    # ------------------------------------------------------------------ #
    # user lifecycle                                                      #
    # ------------------------------------------------------------------ #

    def _handle_list_users(self, options):
        users = User.objects.all().order_by("date_joined")
        if options.get("active_only"):
            users = users.filter(is_active=True)

        users = users.annotate(passkey_count=Count("webauthn_credentials"))

        if options.get("as_json"):
            data = [
                {
                    "username": u.username,
                    "user_id": u.pk,
                    "passkeys": u.passkey_count,
                    "is_active": u.is_active,
                    "unlimited_ai": getattr(getattr(u, "profile", None), "unlimited_ai", False),
                    "date_joined": u.date_joined.strftime("%Y-%m-%d"),
                }
                for u in users
            ]
            self.stdout.write(json.dumps({"ok": True, "users": data}, indent=2))
            return

        self.stdout.write(f"{'USERNAME':<15} {'ID':<6} {'PASSKEYS':<10} {'ACTIVE':<8} {'UNLIMITED':<10} {'JOINED'}")
        self.stdout.write("-" * 70)
        for u in users:
            unlimited = getattr(getattr(u, "profile", None), "unlimited_ai", False)
            self.stdout.write(
                f"{u.username:<15} {u.pk:<6} {u.passkey_count:<10} "
                f"{'yes' if u.is_active else 'no':<8} "
                f"{'yes' if unlimited else 'no':<10} "
                f"{u.date_joined.strftime('%Y-%m-%d')}"
            )
        active = users.filter(is_active=True).count()
        self.stdout.write(f"\nTotal: {users.count()} users ({active} active)")

    def _handle_create_user(self, options):
        from apps.profiles.models import Profile

        username = options["username"]

        if User.objects.filter(username=username).exists():
            self._error(f"User '{username}' already exists.", options)

        user = User.objects.create_user(
            username=username,
            password=None,
            email="",
            is_active=True,
            is_staff=False,
        )
        user.set_unusable_password()
        user.save(update_fields=["password"])

        profile_count = Profile.objects.count()
        Profile.objects.create(
            user=user,
            name=f"User {profile_count + 1}",
            avatar_color=Profile.next_avatar_color(),
        )

        self._success(
            f"Created user '{username}'.",
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

    def _resolve_user_by_username_or_profile_id(self, options):
        from apps.profiles.models import Profile

        username = options.get("username")
        profile_id = options.get("profile_id")

        if username and profile_id:
            self._error("Pass either username or --profile-id, not both.", options)
        if not username and not profile_id:
            self._error("Must pass either username or --profile-id.", options)

        if profile_id:
            try:
                profile = Profile.objects.select_related("user").get(id=profile_id)
            except Profile.DoesNotExist:
                self._error(f"Profile with id {profile_id} not found.", options)
            if not profile.user:
                self._error(f"Profile {profile_id} has no linked user.", options)
            return profile.user
        return self._get_user(username, options)

    def _handle_set_unlimited(self, options):
        user = self._resolve_user_by_username_or_profile_id(options)
        profile = user.profile
        profile.unlimited_ai = True
        profile.save(update_fields=["unlimited_ai"])
        self._success(
            f"Updated {user.username}: unlimited AI access granted",
            options,
            {"username": user.username, "user_id": user.pk, "unlimited_ai": True, "action": "set-unlimited"},
        )

    def _handle_remove_unlimited(self, options):
        user = self._resolve_user_by_username_or_profile_id(options)
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
            json_users = [{k: u[k] for k in ("username", "profile_name", "unlimited_ai", "usage")} for u in users_data]
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
                "unlimited_ai": profile.unlimited_ai,
                "is_exempt": profile.unlimited_ai,
                "usage": get_usage(profile.pk),
            }
            for profile, user in profiles
        ]

    def _print_user_usage(self, u, limits, all_features):
        tag_str = " [unlimited]" if u["unlimited_ai"] else ""
        self.stdout.write(f"{u['username']} ({u['profile_name']}){tag_str}")
        for feature in all_features:
            count = u["usage"][feature]
            suffix = "" if u["is_exempt"] else f"/{limits[feature]}"
            self.stdout.write(f"  {feature}: {count}{suffix}")
        self.stdout.write("")

    def _handle_create_session(self, options):
        import datetime

        from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
        from django.contrib.sessions.backends.db import SessionStore
        from django.utils import timezone

        if options.get("as_json") and not options.get("confirm"):
            self._error(
                f"--confirm flag required for non-interactive create-session. "
                f"Re-run with: cookie_admin create-session {options['username']} --json --confirm",
                options,
            )

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
