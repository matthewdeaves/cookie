"""
Management command to clean up old unused cached search images.

Deletes CachedSearchImage records and files that haven't been accessed
in the specified number of days. Actively used images (displayed in search
or reused during recipe import) are preserved via last_accessed_at updates.

Usage:
    python manage.py cleanup_search_images --days=30
    python manage.py cleanup_search_images --days=30 --dry-run
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.recipes.models import CachedSearchImage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Delete cached search images older than specified days (default: 30)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Delete images not accessed in this many days (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=days)

        # Find old cached images
        old_images = CachedSearchImage.objects.filter(
            last_accessed_at__lt=cutoff_date
        )

        count = old_images.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No cached images older than {days} days found.'
                )
            )
            return

        # Show what will be deleted
        self.stdout.write(
            self.style.WARNING(
                f'Found {count} cached image(s) not accessed since {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")}'
            )
        )

        if dry_run:
            self.stdout.write(
                self.style.NOTICE('\n[DRY RUN] Would delete the following images:')
            )
            for img in old_images[:10]:  # Show first 10
                self.stdout.write(
                    f'  - ID {img.id}: {img.external_url[:80]}... '
                    f'(last accessed: {img.last_accessed_at.strftime("%Y-%m-%d")})'
                )
            if count > 10:
                self.stdout.write(f'  ... and {count - 10} more')

            self.stdout.write(
                self.style.NOTICE(
                    f'\n[DRY RUN] Run without --dry-run to actually delete {count} image(s)'
                )
            )
            return

        # Actually delete the images
        deleted_count = 0
        for img in old_images:
            try:
                # Delete the file from disk if it exists
                if img.image:
                    img.image.delete(save=False)

                # Delete the database record
                img.delete()
                deleted_count += 1
            except Exception as e:
                logger.error(f'Failed to delete cached image {img.id}: {e}')

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully deleted {deleted_count} cached image(s) older than {days} days.'
            )
        )

        if deleted_count < count:
            self.stdout.write(
                self.style.WARNING(
                    f'Warning: {count - deleted_count} image(s) failed to delete. Check logs for details.'
                )
            )
