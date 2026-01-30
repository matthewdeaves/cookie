"""
Django settings for cookie project.
Single settings file for simplicity.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================
# Environment-based Configuration
# ===========================================

DEBUG = os.environ.get("DEBUG", "True").lower() == "true"


def get_secret_key():
    """Get secret key from environment or generate one."""
    env_key = os.environ.get("SECRET_KEY")
    if env_key:
        return env_key
    if DEBUG:
        return "django-insecure-dev-key-change-in-production"
    from django.core.management.utils import get_random_secret_key

    return get_random_secret_key()


SECRET_KEY = get_secret_key()

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

# CSRF trusted origins (for reverse proxies)
csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.profiles",
    "apps.recipes",
    "apps.ai",
    "apps.legacy",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "apps.core.middleware.DeviceDetectionMiddleware",
]

ROOT_URLCONF = "cookie.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "cookie.wsgi.application"

# Support custom database path for Docker volumes
DATABASE_PATH = os.environ.get("DATABASE_PATH", str(BASE_DIR / "db.sqlite3"))

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATABASE_PATH,
        "OPTIONS": {
            # Increase lock wait timeout from default 5s to 20s
            "timeout": 20,
            # Acquire write lock at transaction START (not mid-transaction)
            # This prevents "database is locked" errors during concurrent writes
            # by allowing failed lock acquisitions to be retried
            "transaction_mode": "IMMEDIATE",
            # PRAGMA settings applied on each new connection:
            # - journal_mode=WAL: Allow concurrent reads during writes
            # - synchronous=NORMAL: Safe for WAL mode, better performance
            # - busy_timeout=5000: Wait up to 5s for locks at SQLite level
            "init_command": ("PRAGMA journal_mode=WAL;PRAGMA synchronous=NORMAL;PRAGMA busy_timeout=5000;"),
        },
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Include built frontend assets in static files (only if directory exists)
_frontend_dist = BASE_DIR / "frontend" / "dist"
STATICFILES_DIRS = [_frontend_dist] if _frontend_dist.exists() else []

# WhiteNoise configuration for efficient static file serving
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

MEDIA_URL = "/media/"
data_dir = os.environ.get("DATA_DIR", str(BASE_DIR))
MEDIA_ROOT = Path(data_dir) / "data" / "media" if not DEBUG else BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Session settings
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 43200  # 12 hours

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "apps.recipes": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.recipes.services": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "apps.ai": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
