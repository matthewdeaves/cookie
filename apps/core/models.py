import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from .encryption import decrypt_value, encrypt_value, is_encrypted

# Device code character set: alphanumeric excluding confusables (0, O, 1, I, L)
DEVICE_CODE_CHARS = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"  # pragma: allowlist secret


class AppSettings(models.Model):
    """Singleton model for application-wide settings."""

    # Stored encrypted with 'enc:' prefix
    _openrouter_api_key = models.CharField(max_length=500, blank=True, db_column="openrouter_api_key")
    default_ai_model = models.CharField(max_length=100, default="anthropic/claude-haiku-4.5")

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


class WebAuthnCredential(models.Model):
    """Stored passkey credential for a user."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="webauthn_credentials",
    )
    credential_id = models.BinaryField(max_length=256, unique=True)
    public_key = models.BinaryField(max_length=256)
    sign_count = models.PositiveIntegerField(default=0)
    transports = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"WebAuthnCredential(user={self.user_id}, id={self.pk})"


def generate_device_code():
    """Generate a 6-character code from the confusable-free character set."""
    return "".join(secrets.choice(DEVICE_CODE_CHARS) for _ in range(6))


class DeviceCode(models.Model):
    """Temporary pairing code for the device authorization flow."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("expired", "Expired"),
        ("invalidated", "Invalidated"),
    ]

    code = models.CharField(max_length=6, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    session_key = models.CharField(max_length=40)
    authorizing_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authorized_device_codes",
    )
    attempts_remaining = models.PositiveSmallIntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["session_key"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"DeviceCode({self.code}, status={self.status})"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(seconds=settings.DEVICE_CODE_EXPIRY_SECONDS)
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at
