from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_add_ai_quota_fields"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="devicecode",
            name="attempts_remaining",
        ),
    ]
