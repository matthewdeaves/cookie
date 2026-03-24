"""Admin CLI tool for managing users in public mode."""

import secrets
import string

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Manage Cookie user accounts (public mode only)"

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

        # reset-password
        rp = sub.add_parser("reset-password", help="Reset a user's password")
        rp.add_argument("username")
        rp.add_argument("--password", dest="new_password")
        rp.add_argument("--generate", action="store_true")

        # activate
        a = sub.add_parser("activate", help="Reactivate a user account")
        a.add_argument("username")

        # deactivate
        da = sub.add_parser("deactivate", help="Deactivate a user account")
        da.add_argument("username")

        # cleanup-unverified
        cu = sub.add_parser("cleanup-unverified", help="Delete stale unverified accounts")
        cu.add_argument("--older-than", type=int, default=24)
        cu.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        if settings.AUTH_MODE != "public":
            self.stderr.write("Error: cookie_admin is only available in public mode (AUTH_MODE=public).")
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

        if options.get("as_json"):
            import json

            data = [
                {
                    "username": u.username,
                    "is_admin": u.is_staff,
                    "is_active": u.is_active,
                    "date_joined": u.date_joined.strftime("%Y-%m-%d"),
                }
                for u in users
            ]
            self.stdout.write(json.dumps(data, indent=2))
            return

        self.stdout.write(f"{'USERNAME':<15} {'ADMIN':<7} {'ACTIVE':<8} {'JOINED'}")
        self.stdout.write("-" * 50)
        for u in users:
            status = "" if u.is_active else " (unverified)"
            self.stdout.write(
                f"{u.username:<15} {'yes' if u.is_staff else 'no':<7} "
                f"{'yes' if u.is_active else 'no':<8} "
                f"{u.date_joined.strftime('%Y-%m-%d')}{status}"
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

    def _handle_reset_password(self, options):
        user = self._get_user(options["username"])
        if options.get("generate"):
            pw = "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            user.set_password(pw)
            user.save(update_fields=["password"])
            self.stdout.write(f"Password for '{user.username}' has been reset.\n  New password: {pw}")
            return
        if options.get("new_password"):
            user.set_password(options["new_password"])
            user.save(update_fields=["password"])
            self.stdout.write(f"Password for '{user.username}' has been reset.")
            return
        self.stderr.write("Error: Provide --password <value> or --generate.")
        raise SystemExit(1)

    def _handle_activate(self, options):
        user = self._get_user(options["username"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        self.stdout.write(f"'{user.username}' has been reactivated.")

    def _handle_deactivate(self, options):
        user = self._get_user(options["username"])
        user.is_active = False
        user.save(update_fields=["is_active"])
        self.stdout.write(f"'{user.username}' has been deactivated.")

    def _handle_cleanup_unverified(self, options):
        from django.utils import timezone

        threshold = timezone.now() - timezone.timedelta(hours=options["older_than"])
        stale = User.objects.filter(is_active=False, date_joined__lt=threshold)
        count = stale.count()

        if count == 0:
            self.stdout.write("No unverified accounts found.")
            return

        if options.get("dry_run"):
            self.stdout.write(f"Found {count} unverified account(s) older than {options['older_than']} hours.")
            self.stdout.write("Dry run — no accounts deleted.")
            return

        stale.delete()
        self.stdout.write(f"Deleted {count} unverified account(s) and their associated profiles.")
