"""
Pytest configuration for Cookie tests.

Ensures proper test isolation, especially for async tests that use AsyncClient.
"""

import pytest


@pytest.fixture(autouse=True)
def _clear_cached_search_images(db):
    """
    Clean up CachedSearchImage table before each test.

    CachedSearchImage is a cache table that can accumulate entries across tests
    when async tests use connections outside the test transaction. This fixture
    ensures each test starts with a clean cache table.

    The cleanup is fast (milliseconds) and ensures reliable test isolation.
    """
    from apps.recipes.models import CachedSearchImage

    CachedSearchImage.objects.all().delete()
    yield
    # No cleanup needed after - each test gets a fresh transaction anyway
