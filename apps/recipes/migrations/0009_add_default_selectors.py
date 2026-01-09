"""
Add default CSS selectors for search sources.
These selectors target the main recipe result container on each site.
"""

from django.db import migrations


SELECTOR_UPDATES = {
    'allrecipes.com': 'a.mntl-card-list-items',
    'bbcgoodfood.com': 'article.card',
    'bbc.co.uk': '.gel-layout__item a[href*="/recipes/"]',
    'bonappetit.com': 'a.summary-item__hed-link',
    'budgetbytes.com': 'article.post-summary',
    'delish.com': 'a.full-item-card',
    'epicurious.com': 'article.recipe-card',
    'thepioneerwoman.com': 'a[href*="/recipes/a"]',
    'southernliving.com': 'a[href*="/recipes/"]',
    'skinnytaste.com': 'h2 a',
    'tasty.co': 'a.feed-item',
    'seriouseats.com': 'a.card__title',
    'simplyrecipes.com': 'a.card__titleLink',
    'tasteofhome.com': 'h3.entry-title a',
    'thekitchn.com': 'a.PostCard__link',
}


def add_selectors(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    for host, selector in SELECTOR_UPDATES.items():
        SearchSource.objects.filter(host=host).update(result_selector=selector)


def remove_selectors(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    for host in SELECTOR_UPDATES.keys():
        SearchSource.objects.filter(host=host).update(result_selector='')


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0008_rename_recipes_rec_profile_idx_recipes_rec_profile_7945b8_idx'),
    ]

    operations = [
        migrations.RunPython(add_selectors, remove_selectors),
    ]
