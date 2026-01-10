import pytest
from django.conf import settings


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
