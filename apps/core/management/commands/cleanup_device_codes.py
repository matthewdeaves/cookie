"""Management command to clean up expired device codes."""

from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.core.models import DeviceCode

CLEANUP_CACHE_KEY = "device_code_cleanup_last_run"


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

        counts = {
            "expired": expired.count(),
            "invalidated": invalidated.count(),
            "consumed": consumed.count(),
        }
        total = sum(counts.values())

        if options.get("dry_run"):
            if total == 0:
                self.stdout.write("No device codes to clean up.")
            else:
                self.stdout.write(
                    f"Would delete {total} device codes "
                    f"({counts['expired']} expired, {counts['invalidated']} invalidated, "
                    f"{counts['consumed']} consumed)."
                )
            return

        if total > 0:
            expired.delete()
            invalidated.delete()
            consumed.delete()

        remaining = DeviceCode.objects.count()

        # Record run stats in cache (no expiry — persists until next run)
        cache.set(
            CLEANUP_CACHE_KEY,
            {
                "time": now.isoformat(),
                "deleted": total,
                "remaining": remaining,
                **counts,
            },
            timeout=None,
        )

        if total == 0:
            self.stdout.write("No device codes to clean up.")
        else:
            self.stdout.write(f"Deleted {total} device codes.")
