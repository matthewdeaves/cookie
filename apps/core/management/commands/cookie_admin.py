"""Admin CLI tool for managing users in passkey mode."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db.models import Count


class Command(BaseCommand):
    help = "Manage Cookie user accounts (passkey mode only)"

    def add_arguments(self, parser):
        sub = parser.add_subparsers(dest="subcommand")

        # list-users
        ls = sub.add_parser("list-users", help="List all users")
        ls.add_argument("--active-only", action="store_true")
        ls.add_argument("--admins-only", action="store_true")
        ls.add_argument("--json", action="store_true", dest="as_json")

        # promote
        p = sub.add_parser("promote", help="Grant admin privileges")
        p.add_argument("username")

        # demote
        d = sub.add_parser("demote", help="Revoke admin privileges")
        d.add_argument("username")

        # activate
        a = sub.add_parser("activate", help="Reactivate a user account")
        a.add_argument("username")

        # deactivate
        da = sub.add_parser("deactivate", help="Deactivate a user account")
        da.add_argument("username")

    def handle(self, *args, **options):
        if settings.AUTH_MODE != "passkey":
            self.stderr.write("Error: cookie_admin is only available in passkey mode (AUTH_MODE=passkey).")
            raise SystemExit(2)

        subcommand = options.get("subcommand")
        if not subcommand:
            self.stderr.write("Error: No subcommand provided. Use --help for usage.")
            raise SystemExit(1)

        handler = getattr(self, f"_handle_{subcommand.replace('-', '_')}", None)
        if handler:
            handler(options)
        else:
            self.stderr.write(f"Error: Unknown subcommand '{subcommand}'")
            raise SystemExit(1)

    def _get_user(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            self.stderr.write(f"Error: User '{username}' not found.")
            raise SystemExit(1)

    def _handle_list_users(self, options):
        users = User.objects.all().order_by("date_joined")
        if options.get("active_only"):
            users = users.filter(is_active=True)
        if options.get("admins_only"):
            users = users.filter(is_staff=True)

        users = users.annotate(passkey_count=Count("webauthn_credentials"))

        if options.get("as_json"):
            import json

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
            self.stdout.write(json.dumps(data, indent=2))
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
        user = self._get_user(options["username"])
        if user.is_staff:
            self.stdout.write(f"User '{user.username}' is already an admin.")
            return
        user.is_staff = True
        user.save(update_fields=["is_staff"])
        self.stdout.write(f"'{user.username}' is now an admin.")

    def _handle_demote(self, options):
        user = self._get_user(options["username"])
        if not user.is_staff:
            self.stdout.write(f"User '{user.username}' is not an admin.")
            return
        if User.objects.filter(is_staff=True).count() <= 1:
            self.stderr.write("Error: Cannot demote the last remaining admin. Promote another user first.")
            raise SystemExit(1)
        user.is_staff = False
        user.save(update_fields=["is_staff"])
        self.stdout.write(f"'{user.username}' is no longer an admin.")

    def _handle_activate(self, options):
        user = self._get_user(options["username"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        self.stdout.write(f"'{user.username}' has been reactivated.")

    def _handle_deactivate(self, options):
        user = self._get_user(options["username"])
        user.is_active = False
        user.save(update_fields=["is_active"])
        from django.contrib.sessions.models import Session
        from django.utils import timezone

        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        for session in sessions:
            data = session.get_decoded()
            if str(data.get("_auth_user_id")) == str(user.pk):
                session.delete()
        self.stdout.write(f"'{user.username}' has been deactivated and sessions invalidated.")
