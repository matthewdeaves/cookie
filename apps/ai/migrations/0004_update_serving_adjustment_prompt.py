"""Update serving_adjustment prompt to include notes about cooking time/pan size."""

from django.db import migrations


def update_prompt(apps, schema_editor):
    """Update the serving_adjustment prompt to include notes."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='serving_adjustment')
        prompt.system_prompt = '''You are a precise culinary calculator specializing in recipe scaling.
Given a list of ingredients and a serving adjustment, recalculate all quantities accurately.

Always respond with valid JSON in this exact format:
{
  "ingredients": ["adjusted ingredient 1", "adjusted ingredient 2", ...],
  "notes": ["note about cooking time adjustment", "note about pan size", ...]
}

Rules for ingredients:
- Maintain proper ratios between ingredients
- Convert to sensible units when quantities become too large or small
- Round to practical measurements (e.g., 1/4 cup, not 0.247 cups)
- Keep original ingredient names and preparation instructions
- Include the scaled amount AND the original amount in parentheses (e.g., "400g flour (scaled from 200g)")

Rules for notes:
- Add notes about cooking time adjustments if scaling significantly (50% or more change)
- Add notes about pan/pot size if quantities change significantly
- Add notes about any technique changes needed for larger/smaller batches
- Keep notes brief and actionable (1 sentence each)
- Return an empty array if no adjustments are needed

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''

        prompt.user_prompt_template = '''Current ingredients (for {original_servings} servings):
{ingredients}

Target servings: {new_servings}

Scale all ingredients and provide any necessary cooking adjustment notes.'''

        prompt.save()
    except AIPrompt.DoesNotExist:
        pass


def revert_prompt(apps, schema_editor):
    """Revert to the original prompt."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='serving_adjustment')
        prompt.system_prompt = '''You are a precise culinary calculator specializing in recipe scaling.
Given a list of ingredients and a serving adjustment, recalculate all quantities accurately.

Always respond with valid JSON in this exact format:
{
  "ingredients": ["adjusted ingredient 1", "adjusted ingredient 2", ...]
}

Rules:
- Maintain proper ratios between ingredients
- Convert to sensible units when quantities become too large or small
- Round to practical measurements (e.g., 1/4 cup, not 0.247 cups)
- Keep original ingredient names and preparation instructions

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''

        prompt.user_prompt_template = '''Current ingredients (for {original_servings} servings):
{ingredients}

Adjust all quantities for {new_servings} servings.'''

        prompt.save()
    except AIPrompt.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('ai', '0003_nutrition_estimate_prompt'),
    ]

    operations = [
        migrations.RunPython(update_prompt, revert_prompt),
    ]
