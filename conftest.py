import pytest
from django.conf import settings


# Disable rate limiting in tests — tests don't send X-Forwarded-For headers
# and multiple requests in a single test would be incorrectly rate-limited.
settings.RATELIMIT_ENABLE = False

# Override STORAGES for tests - use simple storage that doesn't require manifest
# The CompressedManifestStaticFilesStorage requires collectstatic to create a manifest
settings.STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@pytest.fixture
def client():
    """Django test client fixture."""
    from django.test import Client

    return Client()
