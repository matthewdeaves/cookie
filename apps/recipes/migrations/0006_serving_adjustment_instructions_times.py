"""Add instructions and time fields to ServingAdjustment for QA-031 and QA-032."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('recipes', '0005_serving_adjustment'),
    ]

    operations = [
        migrations.AddField(
            model_name='servingadjustment',
            name='instructions',
            field=models.JSONField(default=list),
        ),
        migrations.AddField(
            model_name='servingadjustment',
            name='prep_time_adjusted',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servingadjustment',
            name='cook_time_adjusted',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='servingadjustment',
            name='total_time_adjusted',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
