import pytest
from django.conf import settings


# Disable rate limiting in tests — tests don't send X-Forwarded-For headers
# and multiple requests in a single test would be incorrectly rate-limited.
settings.RATELIMIT_ENABLE = False

# Disable SSL redirect in tests — test client doesn't use HTTPS
settings.SECURE_SSL_REDIRECT = False

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


@pytest.fixture
def temp_media_root(settings, tmp_path):
    """Point MEDIA_ROOT at a temp dir so tests that write or wipe media never touch the real one."""
    settings.MEDIA_ROOT = str(tmp_path)
    return tmp_path
