"""Refresh CSS selectors for sources whose search-page HTML changed.

- Delish: card classes are CSS-in-JS hashes that rotate; switch to a structural
  href match (`/cooking/recipe-ideas/aXXXXX/...-recipe/`).
- Serious Eats: search results render as `a.comp.card` again; the prior
  `a.card__title` is gone.
- Skinnytaste: results live inside `<article>` blocks. The old `h2 a` matched
  the title link only, so the parser's neutral-URL "must have image AND
  description" guard rejected every result.
"""

from django.db import migrations


SELECTOR_UPDATES = {
    "delish.com": ('a.full-item-card', 'a[href*="/cooking/recipe-ideas/a"]'),
    "seriouseats.com": ("a.card__title", "a.card"),
    "skinnytaste.com": ("h2 a", "article"),
}


def _apply(apps, mapping):
    SearchSource = apps.get_model("recipes", "SearchSource")
    for host, selector in mapping.items():
        SearchSource.objects.filter(host=host).update(result_selector=selector)


def update_selectors(apps, schema_editor):
    _apply(apps, {host: new for host, (_old, new) in SELECTOR_UPDATES.items()})


def revert_selectors(apps, schema_editor):
    _apply(apps, {host: old for host, (old, _new) in SELECTOR_UPDATES.items()})


class Migration(migrations.Migration):

    dependencies = [
        ("recipes", "0012_add_title_index"),
    ]

    operations = [
        migrations.RunPython(update_selectors, revert_selectors),
    ]
