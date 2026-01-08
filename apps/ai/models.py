from django.db import models


class AIPrompt(models.Model):
    """Stores customizable AI prompts for various features."""

    PROMPT_TYPES = [
        ('recipe_remix', 'Recipe Remix'),
        ('serving_adjustment', 'Serving Adjustment'),
        ('tips_generation', 'Tips Generation'),
        ('discover_favorites', 'Discover from Favorites'),
        ('discover_seasonal', 'Discover Seasonal/Holiday'),
        ('discover_new', 'Discover Try Something New'),
        ('search_ranking', 'Search Result Ranking'),
        ('timer_naming', 'Timer Naming'),
        ('remix_suggestions', 'Remix Suggestions'),
        ('selector_repair', 'CSS Selector Repair'),
    ]

    AVAILABLE_MODELS = [
        # Anthropic Claude
        ('anthropic/claude-3.5-haiku', 'Claude 3.5 Haiku (Fast)'),
        ('anthropic/claude-sonnet-4', 'Claude Sonnet 4'),
        ('anthropic/claude-opus-4', 'Claude Opus 4'),
        ('anthropic/claude-opus-4.5', 'Claude Opus 4.5'),
        # OpenAI GPT
        ('openai/gpt-4o', 'GPT-4o'),
        ('openai/gpt-4o-mini', 'GPT-4o Mini (Fast)'),
        ('openai/gpt-5-mini', 'GPT-5 Mini'),
        ('openai/o3-mini', 'o3 Mini (Reasoning)'),
        # Google Gemini
        ('google/gemini-2.5-pro-preview', 'Gemini 2.5 Pro'),
        ('google/gemini-2.5-flash-preview', 'Gemini 2.5 Flash (Fast)'),
    ]

    prompt_type = models.CharField(
        max_length=50,
        choices=PROMPT_TYPES,
        unique=True,
        help_text='Unique identifier for this prompt type'
    )
    name = models.CharField(
        max_length=100,
        help_text='Human-readable name for this prompt'
    )
    description = models.TextField(
        blank=True,
        help_text='Description of what this prompt does'
    )
    system_prompt = models.TextField(
        help_text='System message sent to the AI model'
    )
    user_prompt_template = models.TextField(
        help_text='User message template with {placeholders} for variable substitution'
    )
    model = models.CharField(
        max_length=100,
        choices=AVAILABLE_MODELS,
        default='anthropic/claude-3.5-haiku',
        help_text='AI model to use for this prompt'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this prompt is enabled'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['prompt_type']
        verbose_name = 'AI Prompt'
        verbose_name_plural = 'AI Prompts'

    def __str__(self):
        return self.name

    def format_user_prompt(self, **kwargs) -> str:
        """Format the user prompt template with provided variables."""
        return self.user_prompt_template.format(**kwargs)

    @classmethod
    def get_prompt(cls, prompt_type: str) -> 'AIPrompt':
        """Get an active prompt by type, raises DoesNotExist if not found."""
        return cls.objects.get(prompt_type=prompt_type, is_active=True)
