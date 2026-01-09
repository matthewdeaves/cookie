"""Update search_ranking prompt to prioritize images."""

from django.db import migrations


def update_search_ranking_prompt(apps, schema_editor):
    """Update the search_ranking prompt to heavily prioritize results with images."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='search_ranking')
        prompt.system_prompt = '''You are a recipe quality evaluator.
Given a list of recipe search results, rank them by relevance and visual appeal.

Always respond with valid JSON as an array of indices (0-based) in ranked order:
[2, 0, 4, 1, 3]

RANKING PRIORITIES (in order of importance):
1. Results WITH images should rank SIGNIFICANTLY higher than those without - this is the most important factor
2. Relevance to the search query
3. Recipe completeness (ratings, reviews)
4. Source reliability

A result with an image that is somewhat relevant should rank HIGHER than a highly relevant result without an image.

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''
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
