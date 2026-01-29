from django.db import models

from .encryption import decrypt_value, encrypt_value, is_encrypted


class AppSettings(models.Model):
    """Singleton model for application-wide settings."""

    # Stored encrypted with 'enc:' prefix
    _openrouter_api_key = models.CharField(
        max_length=500, blank=True, db_column='openrouter_api_key'
    )
    default_ai_model = models.CharField(
        max_length=100, default='anthropic/claude-3.5-haiku'
    )

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

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
