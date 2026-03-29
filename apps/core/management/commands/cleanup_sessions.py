"""Management command to clean up expired sessions with run tracking."""

from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

CLEANUP_CACHE_KEY = "session_cleanup_last_run"


class Command(BaseCommand):
    help = "Delete expired sessions and record run stats"

    def handle(self, *args, **options):
        now = timezone.now()
        expired = Session.objects.filter(expire_date__lt=now)
        count = expired.count()
        expired.delete()
        remaining = Session.objects.count()

        cache.set(
            CLEANUP_CACHE_KEY,
            {"time": now.isoformat(), "deleted": count, "remaining": remaining},
            timeout=None,
        )

        if count:
            self.stdout.write(f"Deleted {count} expired sessions.")
        else:
            self.stdout.write("No expired sessions to clean up.")
