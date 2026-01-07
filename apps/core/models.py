from django.db import models


class AppSettings(models.Model):
    """Singleton model for application-wide settings."""

    openrouter_api_key = models.CharField(max_length=500, blank=True)
    default_ai_model = models.CharField(
        max_length=100, default='anthropic/claude-3.5-haiku'
    )

    class Meta:
        verbose_name = 'App Settings'
        verbose_name_plural = 'App Settings'

    def save(self, *args, **kwargs):
        self.pk = 1  # Enforce singleton
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Get or create the singleton instance."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
