import os

from django.db import models

from .encryption import decrypt_value, encrypt_value, is_encrypted


class AppSettings(models.Model):
    """Singleton model for application-wide settings."""

    DEPLOYMENT_MODE_CHOICES = [
        ("home", "Home Server"),
        ("public", "Public Hosting"),
    ]

    # Stored encrypted with 'enc:' prefix
    _openrouter_api_key = models.CharField(max_length=500, blank=True, db_column="openrouter_api_key")
    default_ai_model = models.CharField(max_length=100, default="anthropic/claude-3.5-haiku")

    # Deployment configuration
    deployment_mode = models.CharField(
        max_length=10,
        choices=DEPLOYMENT_MODE_CHOICES,
        default="home",
    )
    allow_registration = models.BooleanField(default=True)
    instance_name = models.CharField(max_length=100, default="Cookie")

    class Meta:
        verbose_name = "App Settings"
        verbose_name_plural = "App Settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton

        # Encrypt key if not already encrypted
        if self._openrouter_api_key and not is_encrypted(self._openrouter_api_key):
            self._openrouter_api_key = encrypt_value(self._openrouter_api_key)

        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Get or create the singleton instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    @property
    def openrouter_api_key(self) -> str:
        """Get the decrypted API key."""
        return decrypt_value(self._openrouter_api_key)

    @openrouter_api_key.setter
    def openrouter_api_key(self, value: str):
        """Set and encrypt the API key."""
        if value and not is_encrypted(value):
            self._openrouter_api_key = encrypt_value(value)
        else:
            self._openrouter_api_key = value

    def get_deployment_mode(self) -> str:
        """Get deployment mode - env var takes precedence over database."""
        env_mode = os.environ.get("COOKIE_DEPLOYMENT_MODE", "").lower()
        if env_mode in ("home", "public"):
            return env_mode
        return self.deployment_mode

    def get_allow_registration(self) -> bool:
        """Get registration setting - env var takes precedence."""
        env_val = os.environ.get("COOKIE_ALLOW_REGISTRATION", "").lower()
        if env_val in ("true", "false"):
            return env_val == "true"
        return self.allow_registration

    def get_instance_name(self) -> str:
        """Get instance name - env var takes precedence."""
        return os.environ.get("COOKIE_INSTANCE_NAME", "") or self.instance_name
