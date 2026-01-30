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
    image = models.ImageField(upload_to="recipe_images/", blank=True)
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

    # Profile ownership - each recipe belongs to a profile
    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="recipes",
    )

    # Remix tracking
    is_remix = models.BooleanField(default=False)
    remix_profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="remixes",
    )

    # Timestamps
    scraped_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["host"]),
            models.Index(fields=["is_remix"]),
            models.Index(fields=["scraped_at"]),
            models.Index(fields=["profile"]),
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
        ordering = ["name"]

    def __str__(self):
        return self.name


class RecipeFavorite(models.Model):
    """User's favorite recipes, scoped to profile."""

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="favorites",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="favorited_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["profile", "recipe"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.name} - {self.recipe.title}"


class RecipeCollection(models.Model):
    """User-created collection of recipes, scoped to profile."""

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="collections",
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["profile", "name"]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.profile.name} - {self.name}"


class RecipeCollectionItem(models.Model):
    """A recipe within a collection."""

    collection = models.ForeignKey(
        RecipeCollection,
        on_delete=models.CASCADE,
        related_name="items",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["collection", "recipe"]
        ordering = ["order", "-added_at"]

    def __str__(self):
        return f"{self.collection.name} - {self.recipe.title}"


class RecipeViewHistory(models.Model):
    """Tracks recently viewed recipes, scoped to profile."""

    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="view_history",
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
    )
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["profile", "recipe"]
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.profile.name} viewed {self.recipe.title}"


class CachedSearchImage(models.Model):
    """Cached search result image for offline/iOS 9 compatibility."""

    external_url = models.URLField(max_length=2000, unique=True, db_index=True)
    image = models.ImageField(upload_to="search_images/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed_at = models.DateTimeField(auto_now=True)

    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_FAILED, "Failed"),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"Cached: {self.external_url}"


class ServingAdjustment(models.Model):
    """Cached AI-generated serving adjustments per profile."""

    UNIT_SYSTEM_CHOICES = [
        ("metric", "Metric"),
        ("imperial", "Imperial"),
    ]

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name="serving_adjustments",
    )
    profile = models.ForeignKey(
        "profiles.Profile",
        on_delete=models.CASCADE,
        related_name="serving_adjustments",
    )
    target_servings = models.PositiveIntegerField()
    unit_system = models.CharField(
        max_length=10,
        choices=UNIT_SYSTEM_CHOICES,
        default="metric",
    )
    ingredients = models.JSONField(default=list)
    instructions = models.JSONField(default=list)  # QA-031: Scaled instructions
    notes = models.JSONField(default=list)
    prep_time_adjusted = models.PositiveIntegerField(null=True, blank=True)  # QA-032
    cook_time_adjusted = models.PositiveIntegerField(null=True, blank=True)  # QA-032
    total_time_adjusted = models.PositiveIntegerField(null=True, blank=True)  # QA-032
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["recipe", "profile", "target_servings", "unit_system"]
        indexes = [
            models.Index(fields=["recipe", "profile"]),
        ]

    def __str__(self):
        return f"{self.recipe.title} - {self.target_servings} servings ({self.profile.name})"
