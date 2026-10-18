"""List endpoints must not issue per-row queries (selector and collections are loaded on every visit)."""

import pytest
from django.test import Client


def _logged_in_client(profile):
    client = Client()
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


@pytest.mark.django_db
class TestListQueryCounts:
    def test_collections_list_uses_constant_queries(self, django_assert_max_num_queries):
        from apps.profiles.models import Profile
        from apps.recipes.models import Recipe, RecipeCollection, RecipeCollectionItem

        profile = Profile.objects.create(name="Query Counter", avatar_color="#112233")
        recipe = Recipe.objects.create(profile=profile, host="a.com", title="R", ingredients=[], instructions=[])
        for i in range(8):
            collection = RecipeCollection.objects.create(profile=profile, name=f"C{i}")
            RecipeCollectionItem.objects.create(collection=collection, recipe=recipe, order=0)
        client = _logged_in_client(profile)

        # session + profile + collections + prefetched items(+recipes): independent of the collection count
        with django_assert_max_num_queries(6):
            response = client.get("/api/collections/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 8
        assert all(c["recipe_count"] == 1 for c in data)

    def test_profile_selector_stats_are_grouped_not_per_profile(self, django_assert_max_num_queries):
        from apps.profiles.models import Profile

        for i in range(6):
            Profile.objects.create(name=f"P{i}", avatar_color="#112233")

        with django_assert_max_num_queries(10):
            response = Client().get("/api/profiles/")

        assert response.status_code == 200
        assert len(response.json()) == 6
        assert response.json()[0]["stats"]["favorites"] == 0
