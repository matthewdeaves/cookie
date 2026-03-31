"""Remove the search_ranking AI prompt."""

from django.db import migrations


def remove_search_ranking_prompt(apps, schema_editor):
    """Delete the search_ranking prompt."""
    AIPrompt = apps.get_model('ai', 'AIPrompt')
    AIPrompt.objects.filter(prompt_type='search_ranking').delete()


def noop(apps, schema_editor):
    """No-op reverse migration."""
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('ai', '0010_alter_aiprompt_model'),
    ]

    operations = [
        migrations.RunPython(remove_search_ranking_prompt, noop),
    ]
