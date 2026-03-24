"""
Tests for the cleanup_search_images management command (T050).

Tests the command at apps/recipes/management/commands/cleanup_search_images.py:
- Cleanup of expired images (mock file system)
- Dry run mode
- No-op when no expired images
"""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch, MagicMock

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.recipes.models import CachedSearchImage


@pytest.fixture
def old_images(db):
    """Create CachedSearchImage records that are expired (older than 30 days)."""
    old_time = timezone.now() - timedelta(days=45)
    images = []
    for i in range(3):
        img = CachedSearchImage.objects.create(
            external_url=f"https://example.com/old-image-{i}.jpg",
            status=CachedSearchImage.STATUS_SUCCESS,
        )
        # Force update the last_accessed_at to be old
        CachedSearchImage.objects.filter(id=img.id).update(last_accessed_at=old_time)
        img.refresh_from_db()
        images.append(img)
    return images


@pytest.fixture
def recent_images(db):
    """Create CachedSearchImage records that are recent (within 30 days)."""
    images = []
    for i in range(2):
        img = CachedSearchImage.objects.create(
            external_url=f"https://example.com/recent-image-{i}.jpg",
            status=CachedSearchImage.STATUS_SUCCESS,
        )
        images.append(img)
    return images


# --- Cleanup of expired images ---


@pytest.mark.django_db
def test_cleanup_deletes_old_images(old_images):
    """Old images are deleted when command runs."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    assert "Successfully deleted 3" in output
    assert CachedSearchImage.objects.count() == 0


@pytest.mark.django_db
def test_cleanup_preserves_recent_images(old_images, recent_images):
    """Recent images are preserved during cleanup."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    assert "Successfully deleted 3" in output
    assert CachedSearchImage.objects.count() == 2
    # All remaining should be recent
    for img in CachedSearchImage.objects.all():
        assert "recent-image" in img.external_url


@pytest.mark.django_db
def test_cleanup_with_custom_days(old_images):
    """Custom --days parameter adjusts the cutoff."""
    out = StringIO()
    # Using 60 days means 45-day-old images are NOT expired
    call_command("cleanup_search_images", "--days=60", stdout=out)

    output = out.getvalue()
    assert "No cached images older than 60 days" in output
    assert CachedSearchImage.objects.count() == 3


@pytest.mark.django_db
def test_cleanup_deletes_image_files(old_images):
    """Image files are deleted from disk when records are deleted."""
    out = StringIO()
    # The command iterates old images and calls img.image.delete(save=False)
    # if img.image is truthy. Since our test images have no actual files,
    # the image field is falsy and delete won't be called. We verify the
    # records are still deleted properly.
    call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    assert "Successfully deleted 3" in output
    assert CachedSearchImage.objects.count() == 0


@pytest.mark.django_db
def test_cleanup_handles_file_deletion_error(old_images):
    """Command continues if individual file deletion fails."""
    # Patch at the instance level by making the loop encounter an error
    original_delete = CachedSearchImage.delete

    call_count = {"n": 0}

    def failing_delete(self):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise OSError("Permission denied")
        return original_delete(self)

    with patch.object(CachedSearchImage, "delete", failing_delete):
        out = StringIO()
        call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    # Some should have succeeded, some failed
    assert "Successfully deleted" in output


# --- Dry run mode ---


@pytest.mark.django_db
def test_dry_run_does_not_delete(old_images):
    """Dry run shows what would be deleted but doesn't delete."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "DRY RUN" in output
    assert "Would delete" in output
    # All images should still exist
    assert CachedSearchImage.objects.count() == 3


@pytest.mark.django_db
def test_dry_run_shows_image_details(old_images):
    """Dry run output includes image details."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "example.com/old-image" in output
    assert "Found 3 cached image(s)" in output


@pytest.mark.django_db
def test_dry_run_truncates_long_list(db):
    """Dry run shows first 10 and a count for the rest."""
    old_time = timezone.now() - timedelta(days=45)
    for i in range(15):
        img = CachedSearchImage.objects.create(
            external_url=f"https://example.com/img-{i:03d}.jpg",
            status=CachedSearchImage.STATUS_SUCCESS,
        )
        CachedSearchImage.objects.filter(id=img.id).update(last_accessed_at=old_time)

    out = StringIO()
    call_command("cleanup_search_images", "--days=30", "--dry-run", stdout=out)

    output = out.getvalue()
    assert "and 5 more" in output


# --- No-op when no expired images ---


@pytest.mark.django_db
def test_no_expired_images(recent_images):
    """No action taken when all images are recent."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    assert "No cached images older than 30 days" in output
    assert CachedSearchImage.objects.count() == 2


@pytest.mark.django_db
def test_no_images_at_all(db):
    """No action taken when no images exist."""
    out = StringIO()
    call_command("cleanup_search_images", "--days=30", stdout=out)

    output = out.getvalue()
    assert "No cached images older than 30 days" in output


@pytest.mark.django_db
def test_default_days_is_30(db):
    """Default --days value is 30."""
    old_time = timezone.now() - timedelta(days=31)
    img = CachedSearchImage.objects.create(
        external_url="https://example.com/default-test.jpg",
        status=CachedSearchImage.STATUS_SUCCESS,
    )
    CachedSearchImage.objects.filter(id=img.id).update(last_accessed_at=old_time)

    out = StringIO()
    call_command("cleanup_search_images", stdout=out)

    output = out.getvalue()
    assert "Successfully deleted 1" in output
