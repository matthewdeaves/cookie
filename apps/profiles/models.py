from django.db import models


class Profile(models.Model):
    """User profile for the recipe app."""

    THEME_CHOICES = [
        ('light', 'Light'),
        ('dark', 'Dark'),
    ]

    UNIT_CHOICES = [
        ('metric', 'Metric'),
        ('imperial', 'Imperial'),
    ]

    name = models.CharField(max_length=100)
    avatar_color = models.CharField(max_length=7)  # Hex color
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default='light')
    unit_preference = models.CharField(
        max_length=10, choices=UNIT_CHOICES, default='metric'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
