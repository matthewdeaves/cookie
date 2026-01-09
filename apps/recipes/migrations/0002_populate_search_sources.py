from django.db import migrations


SEARCH_SOURCES = [
    {
        'host': 'allrecipes.com',
        'name': 'AllRecipes',
        'search_url_template': 'https://www.allrecipes.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'bbcgoodfood.com',
        'name': 'BBC Good Food',
        'search_url_template': 'https://www.bbcgoodfood.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'bbc.co.uk',
        'name': 'BBC Food',
        'search_url_template': 'https://www.bbc.co.uk/food/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'bonappetit.com',
        'name': 'Bon Appetit',
        'search_url_template': 'https://www.bonappetit.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'budgetbytes.com',
        'name': 'Budget Bytes',
        'search_url_template': 'https://www.budgetbytes.com/?s={query}',
        'result_selector': '',
    },
    {
        'host': 'delish.com',
        'name': 'Delish',
        'search_url_template': 'https://www.delish.com/search/?q={query}',
        'result_selector': '',
    },
    {
        'host': 'epicurious.com',
        'name': 'Epicurious',
        'search_url_template': 'https://www.epicurious.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'thepioneerwoman.com',
        'name': 'The Pioneer Woman',
        'search_url_template': 'https://www.thepioneerwoman.com/food-cooking/recipes/?query={query}',
        'result_selector': '',
    },
    {
        'host': 'southernliving.com',
        'name': 'Southern Living',
        'search_url_template': 'https://www.southernliving.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'skinnytaste.com',
        'name': 'Skinnytaste',
        'search_url_template': 'https://www.skinnytaste.com/?s={query}',
        'result_selector': '',
    },
    {
        'host': 'tasty.co',
        'name': 'Tasty',
        'search_url_template': 'https://tasty.co/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'seriouseats.com',
        'name': 'Serious Eats',
        'search_url_template': 'https://www.seriouseats.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'simplyrecipes.com',
        'name': 'Simply Recipes',
        'search_url_template': 'https://www.simplyrecipes.com/search?q={query}',
        'result_selector': '',
    },
    {
        'host': 'tasteofhome.com',
        'name': 'Taste of Home',
        'search_url_template': 'https://www.tasteofhome.com/recipes/?s={query}',
        'result_selector': '',
    },
    {
        'host': 'thekitchn.com',
        'name': 'The Kitchn',
        'search_url_template': 'https://www.thekitchn.com/search?q={query}',
        'result_selector': '',
    },
]


def populate_search_sources(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    for source_data in SEARCH_SOURCES:
        SearchSource.objects.get_or_create(
            host=source_data['host'],
            defaults=source_data,
        )


def remove_search_sources(apps, schema_editor):
    SearchSource = apps.get_model('recipes', 'SearchSource')
    hosts = [s['host'] for s in SEARCH_SOURCES]
    SearchSource.objects.filter(host__in=hosts).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(populate_search_sources, remove_search_sources),
    ]
