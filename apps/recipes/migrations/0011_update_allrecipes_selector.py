"""
Update AllRecipes CSS selector to match current site HTML.

AllRecipes changed from `a.mntl-card-list-items` to `a.mntl-card` class names.
"""

from django.db import migrations


def update_selector(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    SearchSource.objects.filter(host='allrecipes.com').update(
        result_selector='a.mntl-card'
    )


def revert_selector(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    SearchSource.objects.filter(host='allrecipes.com').update(
        result_selector='a.mntl-card-list-items'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0010_add_remixed_from_field'),
    ]

    operations = [
        migrations.RunPython(update_selector, revert_selector),
    ]
