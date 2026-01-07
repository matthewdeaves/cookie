from django.db import models


class Recipe(models.Model):
    """Recipe model with full recipe-scrapers field support."""

    # Source information
    source_url = models.URLField(max_length=2000, null=True, blank=True, db_index=True)
    canonical_url = models.URLField(max_length=2000, blank=True)
    host = models.CharField(max_length=255)  # e.g., "allrecipes.com"
    site_name = models.CharField(max_length=255, blank=True)

    # Core content
    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)

    # Images (stored locally)
    image = models.ImageField(upload_to='recipe_images/', blank=True)
    image_url = models.URLField(max_length=2000, blank=True)

    # Ingredients
    ingredients = models.JSONField(default=list)
    ingredient_groups = models.JSONField(default=list)

    # Instructions
    instructions = models.JSONField(default=list)
    instructions_text = models.TextField(blank=True)

    # Timing (in minutes)
    prep_time = models.PositiveIntegerField(null=True, blank=True)
    cook_time = models.PositiveIntegerField(null=True, blank=True)
    total_time = models.PositiveIntegerField(null=True, blank=True)

    # Servings
    yields = models.CharField(max_length=100, blank=True)
    servings = models.PositiveIntegerField(null=True, blank=True)

    # Categorization
    category = models.CharField(max_length=100, blank=True)
    cuisine = models.CharField(max_length=100, blank=True)
    cooking_method = models.CharField(max_length=100, blank=True)
    keywords = models.JSONField(default=list)
    dietary_restrictions = models.JSONField(default=list)

    # Equipment and extras
    equipment = models.JSONField(default=list)

    # Nutrition (scraped from source)
    nutrition = models.JSONField(default=dict)

    # Ratings
    rating = models.FloatField(null=True, blank=True)
    rating_count = models.PositiveIntegerField(null=True, blank=True)

    # Language
    language = models.CharField(max_length=10, blank=True)

    # Links
    links = models.JSONField(default=list)

    # AI-generated content
    ai_tips = models.JSONField(default=list, blank=True)

    # Remix tracking
    is_remix = models.BooleanField(default=False)
    remix_profile = models.ForeignKey(
        'profiles.Profile',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='remixes',
    )

    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['host']),
            models.Index(fields=['is_remix']),
            models.Index(fields=['scraped_at']),
        ]

    def __str__(self):
        return self.title


class SearchSource(models.Model):
    """Curated recipe search source."""

    host = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    is_enabled = models.BooleanField(default=True)
    search_url_template = models.CharField(max_length=500)
    result_selector = models.CharField(max_length=255, blank=True)
    logo_url = models.URLField(blank=True)

    # Maintenance tracking
    last_validated_at = models.DateTimeField(null=True, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    needs_attention = models.BooleanField(default=False)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
