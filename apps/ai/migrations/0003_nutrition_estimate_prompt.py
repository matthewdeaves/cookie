"""Add nutrition_estimate prompt for remixed recipes."""

from django.db import migrations


def add_nutrition_prompt(apps, schema_editor):
    """Create the nutrition_estimate prompt."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')

    AIPrompt.objects.create(
        prompt_type='nutrition_estimate',
        name='Nutrition Estimate',
        description='Estimate nutrition values for remixed recipes based on ingredient changes',
        system_prompt='''You are a nutrition expert specializing in recipe analysis.
Given original recipe nutrition data and ingredient changes, estimate the new nutrition values per serving.

IMPORTANT: Respond with ONLY valid JSON, no additional text or explanation.

Use this exact format:
{
  "calories": "X kcal",
  "carbohydrateContent": "X g",
  "proteinContent": "X g",
  "fatContent": "X g",
  "saturatedFatContent": "X g",
  "unsaturatedFatContent": "X g",
  "cholesterolContent": "X mg",
  "sodiumContent": "X mg",
  "fiberContent": "X g"
}

Guidelines:
- Base estimates on the ingredient changes between original and modified recipe
- Account for serving size differences when calculating per-serving values
- Use your knowledge of common ingredient nutrition values
- Round to reasonable precision (whole numbers for calories, 1 decimal for grams)
- If an ingredient swap significantly changes a nutrient (e.g., vegan removes cholesterol), reflect that
- Provide your best estimate even with incomplete information
- Do NOT include any explanation or commentary, ONLY the JSON object''',
        user_prompt_template='''Original Recipe Nutrition (per serving, {original_servings} servings total):
{original_nutrition}

Original Ingredients:
{original_ingredients}

Modified Recipe Ingredients ({new_servings} servings total):
{new_ingredients}

Modification Description: {modification}

Estimate the nutrition values per serving for the modified recipe.''',
        model='anthropic/claude-3.5-haiku',
    )


def remove_nutrition_prompt(apps, schema_editor):
    """Remove the nutrition_estimate prompt."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')
    AIPrompt.objects.filter(prompt_type='nutrition_estimate').delete()


class Migration(migrations.Migration):
    dependencies = [
        ('ai', '0002_seed_prompts'),
    ]

    operations = [
        migrations.RunPython(add_nutrition_prompt, remove_nutrition_prompt),
    ]
