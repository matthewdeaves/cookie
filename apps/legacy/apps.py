"""Legacy app configuration."""

from django.apps import AppConfig


class LegacyConfig(AppConfig):
    """Configuration for the legacy frontend app."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.legacy'
