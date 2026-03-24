"""Delete inactive (unverified) user accounts older than a threshold."""

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Delete unverified user accounts older than a specified number of hours"

    def add_arguments(self, parser):
        parser.add_argument("--older-than", type=int, default=24, help="Age threshold in hours (default: 24)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be deleted without deleting")

    def handle(self, *args, **options):
        if settings.AUTH_MODE != "public":
            self.stderr.write("Error: This command is only available in public mode.")
            raise SystemExit(2)

        threshold = timezone.now() - timezone.timedelta(hours=options["older_than"])
        stale_users = User.objects.filter(is_active=False, date_joined__lt=threshold)
        count = stale_users.count()

        if count == 0:
            self.stdout.write("No unverified accounts found.")
            return

        if options["dry_run"]:
            self.stdout.write(f"Found {count} unverified account(s) older than {options['older_than']} hours.")
            self.stdout.write("Dry run — no accounts deleted.")
            return

        # CASCADE deletes associated profiles
        stale_users.delete()
        self.stdout.write(f"Deleted {count} unverified account(s) and their associated profiles.")
