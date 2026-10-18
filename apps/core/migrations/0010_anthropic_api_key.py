"""Rename the OpenRouter key field to Anthropic and move model ids to Anthropic ids."""

from django.db import migrations, models


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


def rewrite_default_model(apps, schema_editor):
    AppSettings = apps.get_model("core", "AppSettings")
    for row in AppSettings.objects.all():
        new_id = to_anthropic_model_id(row.default_ai_model)
        if new_id != row.default_ai_model:
            AppSettings.objects.filter(pk=row.pk).update(default_ai_model=new_id)


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0009_lower_ai_quota_defaults_further"),
    ]

    operations = [
        # Keeps the (already encrypted) value; the column is renamed with the field.
        migrations.RenameField(
            model_name="appsettings",
            old_name="_openrouter_api_key",
            new_name="_anthropic_api_key",
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="_anthropic_api_key",
            field=models.CharField(blank=True, db_column="anthropic_api_key", max_length=500),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="default_ai_model",
            field=models.CharField(default="claude-haiku-5-5", max_length=100),
        ),
        migrations.RunPython(rewrite_default_model, migrations.RunPython.noop),
    ]
