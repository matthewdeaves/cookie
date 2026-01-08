"""Update serving_adjustment prompt v2 for QA-031 (instructions) and QA-032 (cooking times)."""

from django.db import migrations


def update_prompt(apps, schema_editor):
    """Update the serving_adjustment prompt to include instructions and cooking times."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    try:
        prompt = AIPrompt.objects.get(prompt_type='serving_adjustment')
        prompt.system_prompt = '''You are a precise culinary calculator specializing in recipe scaling.
Given a recipe's ingredients, instructions, and cooking times with a serving adjustment, recalculate all quantities and update instructions accordingly.

Always respond with valid JSON in this exact format:
{
  "ingredients": ["adjusted ingredient 1", "adjusted ingredient 2", ...],
  "instructions": ["adjusted step 1", "adjusted step 2", ...],
  "notes": ["note about cooking time adjustment", "note about pan size", ...],
  "prep_time": "X minutes" or null,
  "cook_time": "X minutes" or null,
  "total_time": "X minutes" or null
}

Rules for ingredients:
- Maintain proper ratios between ingredients
- Convert to sensible units when quantities become too large or small
- Round to practical measurements (e.g., 1/4 cup, not 0.247 cups)
- Keep original ingredient names and preparation instructions
- Include the scaled amount AND the original amount in parentheses (e.g., "400g flour (scaled from 200g)")

Rules for instructions:
- Copy ALL original instruction steps
- Update any quantity references to match the scaled ingredients
- Example: "Add 1 cup flour" becomes "Add 2 cups flour" when doubling
- Keep step numbers and structure the same
- Do not add or remove steps

Rules for cooking times:
- Return null for all time fields if scaling by less than 50% (times unchanged)
- For significant scaling (50% or more), estimate adjusted times
- Larger batches generally need longer cooking times
- Format as "X minutes" or "X hours Y minutes"

Rules for notes:
- Add notes about cooking time adjustments if scaling significantly
- Add notes about pan/pot size if quantities change significantly
- Add notes about any technique changes needed for larger/smaller batches
- Keep notes brief and actionable (1 sentence each)
- Return an empty array if no adjustments are needed

IMPORTANT: Respond with ONLY the JSON, no additional text, explanation, or commentary.'''

        prompt.user_prompt_template = '''Recipe: {title}

Current ingredients (for {original_servings} servings):
{ingredients}

Instructions:
{instructions}

Cooking times:
- Prep time: {prep_time}
- Cook time: {cook_time}
- Total time: {total_time}

Target servings: {new_servings}

Scale all ingredients, update instruction quantities, and provide any necessary cooking time adjustments.'''

        prompt.save()
    except AIPrompt.DoesNotExist:
        pass


def revert_prompt(apps, schema_editor):
    """Revert to the v1 prompt."""
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


class Migration(migrations.Migration):
    dependencies = [
        ('ai', '0004_update_serving_adjustment_prompt'),
    ]

    operations = [
        migrations.RunPython(update_prompt, revert_prompt),
    ]
