from django.db import migrations, models


OLD_DEFAULTS = {
    "daily_limit_remix": 2,
    "daily_limit_remix_suggestions": 3,
    "daily_limit_scale": 5,
    "daily_limit_tips": 5,
    "daily_limit_discover": 1,
    "daily_limit_timer": 10,
}

NEW_DEFAULTS = {
    "daily_limit_remix": 1,
    "daily_limit_remix_suggestions": 2,
    "daily_limit_scale": 2,
    "daily_limit_tips": 2,
    "daily_limit_discover": 1,
    "daily_limit_timer": 3,
}


def apply_new_defaults(apps, schema_editor):
    AppSettings = apps.get_model("core", "AppSettings")
    row = AppSettings.objects.filter(pk=1).first()
    if row is None:
        return
    changed = False
    for field, old_value in OLD_DEFAULTS.items():
        if getattr(row, field) == old_value:
            setattr(row, field, NEW_DEFAULTS[field])
            changed = True
    if changed:
        row.save()


def revert_defaults(apps, schema_editor):
    AppSettings = apps.get_model("core", "AppSettings")
    row = AppSettings.objects.filter(pk=1).first()
    if row is None:
        return
    changed = False
    for field, new_value in NEW_DEFAULTS.items():
        if getattr(row, field) == new_value:
            setattr(row, field, OLD_DEFAULTS[field])
            changed = True
    if changed:
        row.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_lower_ai_quota_defaults"),
    ]

    operations = [
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_remix",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_remix_suggestions",
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_scale",
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_tips",
            field=models.PositiveIntegerField(default=2),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_discover",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name="appsettings",
            name="daily_limit_timer",
            field=models.PositiveIntegerField(default=3),
        ),
        migrations.RunPython(apply_new_defaults, revert_defaults),
    ]
