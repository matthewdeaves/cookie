# Generated migration for adding profile ownership to Recipe

from django.db import migrations, models
import django.db.models.deletion


def delete_all_recipes(apps, schema_editor):
    """Delete all existing recipes since we're adding required profile field."""
    Recipe = apps.get_model('recipes', 'Recipe')
    Recipe.objects.all().delete()


def noop(apps, schema_editor):
    """Reverse is a no-op."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
        ('recipes', '0006_serving_adjustment_instructions_times'),
    ]

    operations = [
        # First add profile field as nullable
        migrations.AddField(
            model_name='recipe',
            name='profile',
            field=models.ForeignKey(
                null=True,
                blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='recipes',
                to='profiles.profile',
            ),
        ),

        # Delete all existing recipes (user said data can be wiped)
        migrations.RunPython(delete_all_recipes, noop),

        # Now make profile field required (non-nullable)
        migrations.AlterField(
            model_name='recipe',
            name='profile',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='recipes',
                to='profiles.profile',
            ),
        ),

        # Add index for profile field
        migrations.AddIndex(
            model_name='recipe',
            index=models.Index(fields=['profile'], name='recipes_rec_profile_idx'),
        ),
    ]
