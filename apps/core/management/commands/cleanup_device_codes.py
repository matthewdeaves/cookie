"""Management command to clean up expired device codes."""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import DeviceCode


class Command(BaseCommand):
    help = "Delete expired and invalidated device codes"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        from django.db import connection

        # Guard against running before migrations have created the table
        table_names = connection.introspection.table_names()
        if "core_devicecode" not in table_names:
            self.stdout.write("DeviceCode table does not exist yet — skipping cleanup.")
            return

        now = timezone.now()
        expired = DeviceCode.objects.filter(expires_at__lt=now, status__in=["pending", "expired"])
        invalidated = DeviceCode.objects.filter(status="invalidated")
        # Also clean authorized codes older than 1 hour (already consumed)
        one_hour_ago = now - timezone.timedelta(hours=1)
        consumed = DeviceCode.objects.filter(status="authorized", created_at__lt=one_hour_ago)

        total = expired.count() + invalidated.count() + consumed.count()

        if total == 0:
            self.stdout.write("No device codes to clean up.")
            return

        if options.get("dry_run"):
            self.stdout.write(
                f"Would delete {total} device codes "
                f"({expired.count()} expired, {invalidated.count()} invalidated, "
                f"{consumed.count()} consumed)."
            )
            return

        expired.delete()
        invalidated.delete()
        consumed.delete()
        self.stdout.write(f"Deleted {total} device codes.")
