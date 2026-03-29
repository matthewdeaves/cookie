"""
Django settings for cookie project.
Single settings file for simplicity.
"""

import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# ===========================================
# Environment-based Configuration
# ===========================================

DEBUG = os.environ.get("DEBUG", "False").lower() == "true"


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

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Use X-Forwarded-Host header (preserves port when behind nginx proxy)
USE_X_FORWARDED_HOST = True

# CSRF trusted origins (for reverse proxies)
csrf_origins = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
CSRF_TRUSTED_ORIGINS = [o.strip() for o in csrf_origins.split(",") if o.strip()]

# ===========================================
# Authentication Mode
# ===========================================
# "home" (default): Profile-based sessions, no user accounts, no login required.
# "passkey": WebAuthn passkey-only authentication with device code flow for legacy devices.
_raw_auth_mode = os.environ.get("AUTH_MODE", "home")
if _raw_auth_mode not in ("home", "passkey"):
    import logging as _logging

    _logging.getLogger("cookie.settings").warning(
        "Unrecognised AUTH_MODE=%r — falling back to 'home'. Valid modes: 'home', 'passkey'.",
        _raw_auth_mode,
    )
    _raw_auth_mode = "home"
AUTH_MODE = _raw_auth_mode
COOKIE_VERSION = os.environ.get("COOKIE_VERSION", "dev")

# ===========================================
# WebAuthn / Passkey Configuration (Passkey Mode)
# ===========================================
WEBAUTHN_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "")  # Derived from request hostname if empty
WEBAUTHN_RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", "Cookie")
DEVICE_CODE_EXPIRY_SECONDS = int(os.environ.get("DEVICE_CODE_EXPIRY_SECONDS", "600"))
DEVICE_CODE_MAX_ATTEMPTS = int(os.environ.get("DEVICE_CODE_MAX_ATTEMPTS", "5"))

INSTALLED_APPS = [
    "django.contrib.auth",
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
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.RequestIDMiddleware",
    "apps.core.middleware.DeviceDetectionMiddleware",
]

# Add Django auth middleware in passkey mode (user accounts required)
if AUTH_MODE == "passkey":
    _session_idx = MIDDLEWARE.index("django.contrib.sessions.middleware.SessionMiddleware")
    MIDDLEWARE.insert(_session_idx + 1, "django.contrib.auth.middleware.AuthenticationMiddleware")

ROOT_URLCONF = "cookie.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "apps.core.context_processors.app_context",
            ],
        },
    },
]

WSGI_APPLICATION = "cookie.wsgi.application"

# Database configuration
# PostgreSQL is required — no SQLite fallback.
# conn_max_age=60 and conn_health_checks=True are appropriate for single-server
# deployment with Gunicorn. Upgrade path: use pgbouncer for multi-server.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL environment variable is required. "
        "Set it to a PostgreSQL connection string, "
        "e.g. postgres://user:pass@host:5432/dbname"  # pragma: allowlist secret
    )

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=60,
        conn_health_checks=True,
    )
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

# Cache configuration — database-backed for sharing across Gunicorn workers
CACHES = {
    "default": {
        "BACKEND": "apps.core.cache.PostgreSafeDatabaseCache",
        "LOCATION": "django_cache",
    }
}

# Search result cache: 5 days (shared globally across all profiles)
SEARCH_CACHE_TIMEOUT = 432000  # 5 days in seconds

# Session settings
# Database-backed sessions: intentional for single-server deployment.
# Upgrade path: switch to django.contrib.sessions.backends.cache with Redis
# for multi-server deployments.
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 43200  # 12 hours
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_HTTPONLY = False  # SPA reads CSRF cookie via JavaScript

CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"

# Production security hardening (inactive in development)
if not DEBUG:
    SECURE_HSTS_SECONDS = 63072000  # 2 years, matching nginx.prod.conf
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "true").lower() == "true"
    SECURE_REDIRECT_EXEMPT = [r"^api/system/health/$", r"^api/system/ready/$"]
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Rate limiting (django-ratelimit)
# Use a callable that safely extracts the first IP from X-Forwarded-For,
# handling multi-proxy chains (Cloudflare → Traefik → nginx → Django).
RATELIMIT_IP_META_KEY = "apps.core.middleware.get_client_ip"

# Logging configuration
LOG_FORMAT = os.environ.get("LOG_FORMAT", "text")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

_log_formatter = "json" if LOG_FORMAT == "json" else "verbose"

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
        "json": {
            "()": "apps.core.logging.JSONFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": _log_formatter,
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
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "security": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
}
