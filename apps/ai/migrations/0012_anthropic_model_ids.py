"""Switch AIPrompt models from OpenRouter ids to Anthropic API model ids."""

from django.db import migrations, models

CHOICES = [
    ("claude-haiku-5-5", "Claude Haiku 5.5 (Fast)"),
    ("claude-sonnet-5-5", "Claude Sonnet 5.5"),
    ("claude-opus-5-5", "Claude Opus 5.5"),
]


def to_anthropic_model_id(model_id):
    """Map an OpenRouter-style model id to the nearest Anthropic API model id."""
    if not model_id or model_id.startswith("claude-"):
        return model_id or "claude-haiku-5-5"
    if model_id.startswith("anthropic/"):
        name = model_id.split("/", 1)[1].lower()
        if "opus" in name:
            return "claude-opus-5-5"
        if "sonnet" in name:
            return "claude-sonnet-5-5"
    return "claude-haiku-5-5"


def rewrite_prompt_models(apps, schema_editor):
    AIPrompt = apps.get_model("ai", "AIPrompt")
    for row in AIPrompt.objects.all():
        new_id = to_anthropic_model_id(row.model)
        if new_id != row.model:
            AIPrompt.objects.filter(pk=row.pk).update(model=new_id)


class Migration(migrations.Migration):
    dependencies = [
        ("ai", "0011_remove_search_ranking_prompt"),
    ]

    operations = [
        migrations.AlterField(
            model_name="aiprompt",
            name="model",
            field=models.CharField(
                choices=CHOICES,
                default="claude-haiku-5-5",
                help_text="AI model to use for this prompt",
                max_length=100,
            ),
        ),
        migrations.RunPython(rewrite_prompt_models, migrations.RunPython.noop),
    ]
