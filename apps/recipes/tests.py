"""
Tests for recipe user features: collections, favorites, and history.
"""

import json

from django.test import TestCase, Client

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeFavorite,
    RecipeViewHistory,
)


class BaseTestCase(TestCase):
    """Base test case with common setup."""

    def setUp(self):
        self.client = Client()
        self.profile = Profile.objects.create(
            name="Test User",
            avatar_color="#d97850",
        )
        self.recipe = Recipe.objects.create(
            profile=self.profile,
            title="Chocolate Chip Cookies",
            host="example.com",
            canonical_url="https://example.com/cookies",
            ingredients=["flour", "sugar", "chocolate chips"],
            instructions=["Mix ingredients", "Bake at 350F"],
        )
        self.recipe2 = Recipe.objects.create(
            profile=self.profile,
            title="Vanilla Cake",
            host="example.com",
            canonical_url="https://example.com/cake",
            ingredients=["flour", "sugar", "vanilla"],
            instructions=["Mix", "Bake"],
        )
        # Select profile in session
        session = self.client.session
        session["profile_id"] = self.profile.id
        session.save()


class CollectionTests(BaseTestCase):
    """Tests for collection CRUD operations."""

    def test_list_collections_empty(self):
        """List collections returns empty list initially."""
        response = self.client.get("/api/collections/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_create_collection(self):
        """Create a new collection."""
        response = self.client.post(
            "/api/collections/",
            data=json.dumps({"name": "Desserts", "description": "Sweet treats"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["name"], "Desserts")
        self.assertEqual(data["description"], "Sweet treats")
        self.assertEqual(data["recipe_count"], 0)

    def test_create_collection_duplicate_name(self):
        """Creating a collection with duplicate name fails."""
        RecipeCollection.objects.create(
            profile=self.profile,
            name="Desserts",
        )
        response = self.client.post(
            "/api/collections/",
            data=json.dumps({"name": "Desserts"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_list_collections(self):
        """List collections returns existing collections."""
        RecipeCollection.objects.create(profile=self.profile, name="Desserts")
        RecipeCollection.objects.create(profile=self.profile, name="Quick Meals")

        response = self.client.get("/api/collections/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_get_collection(self):
        """Get a single collection with its recipes."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Baking",
            description="Baked goods",
        )
        RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=self.recipe,
            order=1,
        )

        response = self.client.get(f"/api/collections/{collection.id}/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["name"], "Baking")
        self.assertEqual(len(data["recipes"]), 1)
        self.assertEqual(data["recipes"][0]["recipe"]["title"], "Chocolate Chip Cookies")

    def test_get_collection_not_found(self):
        """Getting a non-existent collection returns 404."""
        response = self.client.get("/api/collections/999/")
        self.assertEqual(response.status_code, 404)

    def test_update_collection(self):
        """Update a collection's name and description."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Desserts",
        )

        response = self.client.put(
            f"/api/collections/{collection.id}/",
            data=json.dumps({"name": "Sweet Desserts", "description": "Updated"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data["name"], "Sweet Desserts")
        self.assertEqual(data["description"], "Updated")

    def test_delete_collection(self):
        """Delete a collection."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="To Delete",
        )

        response = self.client.delete(f"/api/collections/{collection.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(RecipeCollection.objects.filter(id=collection.id).exists())

    def test_add_recipe_to_collection(self):
        """Add a recipe to a collection."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Baking",
        )

        response = self.client.post(
            f"/api/collections/{collection.id}/recipes/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["recipe"]["title"], "Chocolate Chip Cookies")
        self.assertEqual(data["order"], 1)

    def test_add_recipe_to_collection_increments_order(self):
        """Adding recipes to a collection increments their order."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Baking",
        )
        RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=self.recipe,
            order=1,
        )

        response = self.client.post(
            f"/api/collections/{collection.id}/recipes/",
            data=json.dumps({"recipe_id": self.recipe2.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["order"], 2)

    def test_add_duplicate_recipe_to_collection(self):
        """Adding the same recipe twice fails."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Baking",
        )
        RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=self.recipe,
            order=1,
        )

        response = self.client.post(
            f"/api/collections/{collection.id}/recipes/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_remove_recipe_from_collection(self):
        """Remove a recipe from a collection."""
        collection = RecipeCollection.objects.create(
            profile=self.profile,
            name="Baking",
        )
        RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=self.recipe,
            order=1,
        )

        response = self.client.delete(f"/api/collections/{collection.id}/recipes/{self.recipe.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(RecipeCollectionItem.objects.filter(collection=collection, recipe=self.recipe).exists())

    def test_collection_isolation_between_profiles(self):
        """Collections are isolated between profiles."""
        other_profile = Profile.objects.create(
            name="Other User",
            avatar_color="#8fae6f",
        )
        other_collection = RecipeCollection.objects.create(
            profile=other_profile,
            name="Other Collection",
        )

        # Should not see other profile's collection
        response = self.client.get("/api/collections/")
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)

        # Should not be able to access other profile's collection
        response = self.client.get(f"/api/collections/{other_collection.id}/")
        self.assertEqual(response.status_code, 404)


class FavoriteTests(BaseTestCase):
    """Tests for favorites functionality."""

    def test_list_favorites_empty(self):
        """List favorites returns empty list initially."""
        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_add_favorite(self):
        """Add a recipe to favorites."""
        response = self.client.post(
            "/api/favorites/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["recipe"]["title"], "Chocolate Chip Cookies")

    def test_add_duplicate_favorite(self):
        """Adding the same recipe twice fails."""
        RecipeFavorite.objects.create(
            profile=self.profile,
            recipe=self.recipe,
        )

        response = self.client.post(
            "/api/favorites/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_list_favorites(self):
        """List favorites returns favorited recipes."""
        RecipeFavorite.objects.create(profile=self.profile, recipe=self.recipe)
        RecipeFavorite.objects.create(profile=self.profile, recipe=self.recipe2)

        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_remove_favorite(self):
        """Remove a recipe from favorites."""
        RecipeFavorite.objects.create(
            profile=self.profile,
            recipe=self.recipe,
        )

        response = self.client.delete(f"/api/favorites/{self.recipe.id}/")
        self.assertEqual(response.status_code, 204)
        self.assertFalse(RecipeFavorite.objects.filter(profile=self.profile, recipe=self.recipe).exists())

    def test_remove_favorite_not_found(self):
        """Removing a non-favorited recipe returns 404."""
        response = self.client.delete(f"/api/favorites/{self.recipe.id}/")
        self.assertEqual(response.status_code, 404)

    def test_favorites_isolation_between_profiles(self):
        """Favorites are isolated between profiles."""
        other_profile = Profile.objects.create(
            name="Other User",
            avatar_color="#8fae6f",
        )
        RecipeFavorite.objects.create(
            profile=other_profile,
            recipe=self.recipe,
        )

        # Should not see other profile's favorites
        response = self.client.get("/api/favorites/")
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)


class HistoryTests(BaseTestCase):
    """Tests for view history functionality."""

    def test_list_history_empty(self):
        """List history returns empty list initially."""
        response = self.client.get("/api/history/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.content), [])

    def test_record_view(self):
        """Record a recipe view."""
        response = self.client.post(
            "/api/history/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertEqual(data["recipe"]["title"], "Chocolate Chip Cookies")

    def test_record_view_updates_timestamp(self):
        """Recording the same view updates the timestamp."""
        self.client.post(
            "/api/history/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )

        # Record again - should return 200, not 201
        response = self.client.post(
            "/api/history/",
            data=json.dumps({"recipe_id": self.recipe.id}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)

        # Should still only have one history entry
        self.assertEqual(RecipeViewHistory.objects.filter(profile=self.profile).count(), 1)

    def test_list_history(self):
        """List history returns viewed recipes."""
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe)
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe2)

        response = self.client.get("/api/history/")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 2)

    def test_list_history_with_limit(self):
        """List history respects limit parameter."""
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe)
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe2)

        response = self.client.get("/api/history/?limit=1")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(len(data), 1)

    def test_clear_history(self):
        """Clear all view history."""
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe)
        RecipeViewHistory.objects.create(profile=self.profile, recipe=self.recipe2)

        response = self.client.delete("/api/history/")
        self.assertEqual(response.status_code, 204)
        self.assertEqual(RecipeViewHistory.objects.filter(profile=self.profile).count(), 0)

    def test_history_isolation_between_profiles(self):
        """History is isolated between profiles."""
        other_profile = Profile.objects.create(
            name="Other User",
            avatar_color="#8fae6f",
        )
        RecipeViewHistory.objects.create(
            profile=other_profile,
            recipe=self.recipe,
        )

        # Should not see other profile's history
        response = self.client.get("/api/history/")
        data = json.loads(response.content)
        self.assertEqual(len(data), 0)


class NoProfileTests(TestCase):
    """Tests for endpoints when no profile is selected."""

    def setUp(self):
        self.client = Client()
        # Create a profile to own the recipe (not selected in session)
        self.temp_profile = Profile.objects.create(
            name="Temp User",
            avatar_color="#d97850",
        )
        self.recipe = Recipe.objects.create(
            profile=self.temp_profile,
            title="Test Recipe",
            host="example.com",
            canonical_url="https://example.com/recipe",
        )

    def test_favorites_requires_profile(self):
        """Favorites endpoints require a selected profile."""
        response = self.client.get("/api/favorites/")
        self.assertEqual(response.status_code, 404)

    def test_collections_requires_profile(self):
        """Collections endpoints require a selected profile."""
        response = self.client.get("/api/collections/")
        self.assertEqual(response.status_code, 404)

    def test_history_requires_profile(self):
        """History endpoints require a selected profile."""
        response = self.client.get("/api/history/")
        self.assertEqual(response.status_code, 404)


class QuantityTidyingTests(TestCase):
    """Tests for ingredient quantity tidying utilities (QA-029)."""

    def test_decimal_to_fraction_half(self):
        """Convert 0.5 to 1/2."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(0.5), "1/2")

    def test_decimal_to_fraction_quarter(self):
        """Convert 0.25 to 1/4."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(0.25), "1/4")

    def test_decimal_to_fraction_third(self):
        """Convert 0.333... to 1/3."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(0.333), "1/3")
        self.assertEqual(decimal_to_fraction(0.33), "1/3")

    def test_decimal_to_fraction_two_thirds(self):
        """Convert 0.666... to 2/3."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(0.666), "2/3")
        self.assertEqual(decimal_to_fraction(0.67), "2/3")

    def test_decimal_to_fraction_three_quarters(self):
        """Convert 0.75 to 3/4."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(0.75), "3/4")

    def test_decimal_to_fraction_mixed_number(self):
        """Convert 1.5 to 1 1/2."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(1.5), "1 1/2")
        self.assertEqual(decimal_to_fraction(2.25), "2 1/4")
        self.assertEqual(decimal_to_fraction(1.333), "1 1/3")

    def test_decimal_to_fraction_whole_number(self):
        """Whole numbers stay as-is."""
        from apps.recipes.utils import decimal_to_fraction

        self.assertEqual(decimal_to_fraction(2.0), "2")
        self.assertEqual(decimal_to_fraction(3.0), "3")

    def test_tidy_ingredient_cups(self):
        """Tidy cup measurements."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("0.5 cup sugar"), "1/2 cup sugar")
        self.assertEqual(tidy_ingredient("1.5 cups flour"), "1 1/2 cups flour")
        self.assertEqual(tidy_ingredient("0.333 cup milk"), "1/3 cup milk")

    def test_tidy_ingredient_tablespoons(self):
        """Tidy tablespoon measurements."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("0.5 tablespoon oil"), "1/2 tablespoon oil")
        self.assertEqual(tidy_ingredient("1.5 tbsp butter"), "1 1/2 tbsp butter")

    def test_tidy_ingredient_teaspoons(self):
        """Tidy teaspoon measurements."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("0.25 teaspoon salt"), "1/4 teaspoon salt")
        self.assertEqual(tidy_ingredient("0.5 tsp vanilla"), "1/2 tsp vanilla")

    def test_tidy_ingredient_keeps_grams(self):
        """Grams should stay as decimals."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("225g butter"), "225 g butter")
        self.assertEqual(tidy_ingredient("150.5 grams flour"), "150.5 grams flour")

    def test_tidy_ingredient_keeps_ml(self):
        """Milliliters should stay as decimals."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("250 ml milk"), "250 ml milk")
        self.assertEqual(tidy_ingredient("37.5 ml water"), "37.5 ml water")

    def test_tidy_ingredient_countable_items(self):
        """Countable items get fractions."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("1.5 cloves garlic"), "1 1/2 cloves garlic")
        self.assertEqual(tidy_ingredient("0.5 bunch parsley"), "1/2 bunch parsley")

    def test_tidy_ingredient_no_unit(self):
        """Ingredients without recognized units get tidied."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("1.5 large eggs"), "1 1/2 large eggs")
        self.assertEqual(tidy_ingredient("0.5 medium onion"), "1/2 medium onion")

    def test_tidy_quantities_list(self):
        """Tidy a list of ingredients."""
        from apps.recipes.utils import tidy_quantities

        ingredients = [
            "0.5 cup sugar",
            "1.333 cups flour",
            "225g butter",
            "0.25 teaspoon salt",
        ]
        result = tidy_quantities(ingredients)
        self.assertEqual(result[0], "1/2 cup sugar")
        self.assertEqual(result[1], "1 1/3 cups flour")
        self.assertEqual(result[2], "225 g butter")
        self.assertEqual(result[3], "1/4 teaspoon salt")

    def test_tidy_ingredient_empty_string(self):
        """Empty string returns empty string."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient(""), "")

    def test_tidy_ingredient_no_number(self):
        """Ingredient without number returns as-is."""
        from apps.recipes.utils import tidy_ingredient

        self.assertEqual(tidy_ingredient("salt to taste"), "salt to taste")
        self.assertEqual(tidy_ingredient("fresh parsley"), "fresh parsley")
