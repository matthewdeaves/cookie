"""Update search_ranking prompt to prioritize images."""

from django.db import migrations


def update_search_ranking_prompt(apps, schema_editor):
    """Update the search_ranking prompt to heavily prioritize results with images."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='search_ranking')
        prompt.system_prompt = '''You are a recipe search ranker.

CRITICAL RULE: ALL results with [has image] MUST appear BEFORE any results without images. This is NON-NEGOTIABLE.

Within each group (with images vs without images), rank by:
1. Relevance to the search query
2. Recipe completeness (ratings, reviews)
3. Source reliability

Output format: JSON array of 0-based indices in ranked order.
Example: [2, 0, 4, 1, 3]

IMPORTANT: Output ONLY the JSON array. No explanation or text.'''
        prompt.save()
    except AIPrompt.DoesNotExist:
        pass


def reverse_update(apps, schema_editor):
    """Revert to original prompt."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='search_ranking')
        prompt.system_prompt = '''You are a recipe quality evaluator.
Given a list of recipe search results, rank them by relevance and quality.

Always respond with valid JSON as an array of indices (0-based) in ranked order:
[2, 0, 4, 1, 3]

Consider:
- Relevance to the search query
- Recipe completeness (has image, ratings, reviews)
- Source reliability
- Clarity of title and description

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''
        prompt.save()
    except AIPrompt.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0006_add_ai_discovery_suggestion'),
    ]

    operations = [
        migrations.RunPython(update_search_ranking_prompt, reverse_update),
    ]
