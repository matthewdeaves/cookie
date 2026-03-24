from django.conf import settings
from django.db import models


AVATAR_COLORS = [
    "#d97850",  # burnt orange
    "#8fae6f",  # sage green
    "#6b9dad",  # teal
    "#9d80b8",  # purple
    "#d16b6b",  # coral red
    "#e6a05f",  # amber
    "#6bb8a5",  # mint
    "#c77a9e",  # rose
    "#7d9e6f",  # olive
    "#5b8abf",  # steel blue
]


class Profile(models.Model):
    """User profile for the recipe app."""

    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
    ]

    UNIT_CHOICES = [
        ("metric", "Metric"),
        ("imperial", "Imperial"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    name = models.CharField(max_length=100)
    avatar_color = models.CharField(max_length=7)  # Hex color
    theme = models.CharField(max_length=10, choices=THEME_CHOICES, default="light")
    unit_preference = models.CharField(max_length=10, choices=UNIT_CHOICES, default="metric")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @classmethod
    def next_avatar_color(cls):
        """Return the next unused color from the palette, cycling if needed."""
        used_colors = set(cls.objects.values_list("avatar_color", flat=True))
        for color in AVATAR_COLORS:
            if color not in used_colors:
                return color
        # All used - cycle based on count
        return AVATAR_COLORS[cls.objects.count() % len(AVATAR_COLORS)]
