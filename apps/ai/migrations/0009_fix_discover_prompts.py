"""Fix discover prompts to return arrays instead of single objects.

The validator expects arrays of 1-5 items, but the prompts were instructing
the AI to return a single object. This caused validation failures and
"No suggestions yet" on the Discover tab.

Fixes QA-057.
"""

from django.db import migrations


# New prompts that request arrays of 3-5 suggestions
DISCOVER_SEASONAL_PROMPT = '''You are a culinary calendar expert.
Based on the current date and season, suggest 3-5 appropriate recipes.

Always respond with valid JSON as an array of 3-5 suggestions:
[
  {"search_query": "specific seasonal dish", "title": "Suggestion Title", "description": "Why this is perfect for the season"},
  ...
]

Consider:
- Current season and weather
- Upcoming holidays within the next 2 weeks
- Seasonal ingredient availability
- Traditional dishes for the time of year

Provide varied suggestions (different cuisines, dish types, or occasions).

IMPORTANT: Respond with ONLY the JSON array, no additional text.'''

DISCOVER_FAVORITES_PROMPT = '''You are a culinary recommendation engine.
Based on a user's recipe history, suggest 3-5 new recipes they might enjoy.

Always respond with valid JSON as an array of 3-5 suggestions:
[
  {"search_query": "specific dish name", "title": "Suggestion Title", "description": "Why they might enjoy this"},
  ...
]

The search_query should be specific dish names or cuisine types matching their preferences.
Provide varied suggestions based on different aspects of their history.
Keep descriptions concise (1-2 sentences).

IMPORTANT: Respond with ONLY the JSON array, no additional text.'''

DISCOVER_NEW_PROMPT = '''You are a culinary adventure guide.
Based on a user's cooking history, suggest 3-5 new and different dishes they haven't tried.

Always respond with valid JSON as an array of 3-5 suggestions:
[
  {"search_query": "specific dish from different cuisine", "title": "Adventure Title", "description": "Why this would be a fun culinary adventure"},
  ...
]

Suggest dishes that:
- Are from cuisines they haven't explored
- Use techniques they might not have tried
- Introduce new flavors while remaining accessible
- Are achievable for a home cook

Provide varied adventures (different cuisines, techniques, or flavor profiles).

IMPORTANT: Respond with ONLY the JSON array, no additional text.'''


# Original prompts for rollback
ORIGINAL_DISCOVER_SEASONAL = '''You are a culinary calendar expert.
Based on the current date and season, suggest an appropriate recipe.

Always respond with valid JSON in this exact format:
{
  "search_query": "specific seasonal dish or recipe name",
  "title": "Seasonal Suggestion Title",
  "description": "Brief explanation of why this is perfect for the season"
}

Consider:
- Current season and weather
- Upcoming holidays within the next 2 weeks
- Seasonal ingredient availability
- Traditional dishes for the time of year

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''

ORIGINAL_DISCOVER_FAVORITES = '''You are a culinary recommendation engine.
Based on a user's favorite recipes, suggest a new recipe they might enjoy.

Always respond with valid JSON in this exact format:
{
  "search_query": "specific search query to find similar recipes",
  "title": "Suggested Recipe Category",
  "description": "Brief explanation of why this suggestion fits their taste"
}

The search_query should be a specific dish name or cuisine type that matches their preferences.
Keep descriptions concise (1-2 sentences).

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''

ORIGINAL_DISCOVER_NEW = '''You are a culinary adventure guide.
Based on a user's cooking history, suggest something new and different they haven't tried.

Always respond with valid JSON in this exact format:
{
  "search_query": "specific dish from a different cuisine or technique",
  "title": "Adventure Suggestion Title",
  "description": "Brief explanation of why this would be a fun culinary adventure"
}

Suggest dishes that:
- Are from cuisines they haven't explored
- Use techniques they might not have tried
- Introduce new flavors while remaining accessible
- Are achievable for a home cook

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''


def update_discover_prompts(apps, schema_editor):
    """Update discover prompts to request arrays of 3-5 suggestions."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    prompts_to_update = [
        ('discover_seasonal', DISCOVER_SEASONAL_PROMPT),
        ('discover_favorites', DISCOVER_FAVORITES_PROMPT),
        ('discover_new', DISCOVER_NEW_PROMPT),
    ]

    for prompt_type, new_prompt in prompts_to_update:
        try:
            prompt = AIPrompt.objects.get(prompt_type=prompt_type)
            prompt.system_prompt = new_prompt
            prompt.save()
        except AIPrompt.DoesNotExist:
            pass


def reverse_update(apps, schema_editor):
    """Revert to original single-object prompts."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    prompts_to_revert = [
        ('discover_seasonal', ORIGINAL_DISCOVER_SEASONAL),
        ('discover_favorites', ORIGINAL_DISCOVER_FAVORITES),
        ('discover_new', ORIGINAL_DISCOVER_NEW),
    ]

    for prompt_type, original_prompt in prompts_to_revert:
        try:
            prompt = AIPrompt.objects.get(prompt_type=prompt_type)
            prompt.system_prompt = original_prompt
            prompt.save()
        except AIPrompt.DoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0008_update_serving_adjustment_indivisible'),
    ]

    operations = [
        migrations.RunPython(update_discover_prompts, reverse_update),
    ]
