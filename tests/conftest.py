"""
Pytest configuration for Cookie tests.

Ensures proper test isolation, especially for async tests that use AsyncClient.
"""

import pytest


@pytest.fixture(autouse=True)
def _default_home_mode(monkeypatch):
    """
    Set default deployment mode to 'home' for tests.

    The docker-compose.override.yml may set COOKIE_DEPLOYMENT_MODE=public
    for local development testing. This fixture ensures tests run in home
    mode by default, but individual tests can override via their own
    monkeypatch.setenv() calls which run after this fixture.

    Note: Tests that need public mode should call:
        monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "public")
    at the START of their test function, before any code that checks
    the deployment mode.
    """
    import os

    # Always set to home mode - individual tests can override
    monkeypatch.setenv("COOKIE_DEPLOYMENT_MODE", "home")

    # Clear COOKIE_ALLOW_REGISTRATION so tests get the database default
    # (docker-compose.override.yml may set this to true for dev testing)
    monkeypatch.delenv("COOKIE_ALLOW_REGISTRATION", raising=False)


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
