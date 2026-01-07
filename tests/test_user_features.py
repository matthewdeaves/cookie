"""
Tests for user features: favorites, collections, history, and profile isolation.
"""

import pytest
from django.test import Client

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeFavorite,
    RecipeViewHistory,
)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def profile_a(db):
    """Create first test profile."""
    return Profile.objects.create(name='Profile A', avatar_color='#ff0000')


@pytest.fixture
def profile_b(db):
    """Create second test profile."""
    return Profile.objects.create(name='Profile B', avatar_color='#00ff00')


@pytest.fixture
def recipe(db):
    """Create a test recipe."""
    return Recipe.objects.create(
        host='test.com',
        title='Test Recipe',
    )


@pytest.fixture
def recipe2(db):
    """Create a second test recipe."""
    return Recipe.objects.create(
        host='test.com',
        title='Another Recipe',
    )


def select_profile(client, profile):
    """Helper to select a profile in the session."""
    client.post(f'/api/profiles/{profile.id}/select/')


# =============================================================================
# Favorites API Tests
# =============================================================================

@pytest.mark.django_db
class TestFavoritesAPI:
    """Tests for favorites endpoints."""

    def test_list_favorites_requires_profile(self, client):
        """List favorites returns 404 when no profile selected."""
        response = client.get('/api/favorites/')
        assert response.status_code == 404

    def test_list_favorites_empty(self, client, profile_a):
        """List favorites returns empty list for new profile."""
        select_profile(client, profile_a)
        response = client.get('/api/favorites/')
        assert response.status_code == 200
        assert response.json() == []

    def test_add_favorite(self, client, profile_a, recipe):
        """Add a recipe to favorites."""
        select_profile(client, profile_a)
        response = client.post(
            '/api/favorites/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 201
        assert response.json()['recipe']['id'] == recipe.id

    def test_add_favorite_duplicate(self, client, profile_a, recipe):
        """Adding same recipe twice returns error."""
        select_profile(client, profile_a)
        client.post(
            '/api/favorites/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        response = client.post(
            '/api/favorites/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'already a favorite' in response.json()['detail']

    def test_remove_favorite(self, client, profile_a, recipe):
        """Remove a recipe from favorites."""
        select_profile(client, profile_a)
        RecipeFavorite.objects.create(profile=profile_a, recipe=recipe)

        response = client.delete(f'/api/favorites/{recipe.id}/')
        assert response.status_code == 204
        assert not RecipeFavorite.objects.filter(
            profile=profile_a, recipe=recipe
        ).exists()

    def test_remove_nonexistent_favorite(self, client, profile_a):
        """Removing non-existent favorite returns 404."""
        select_profile(client, profile_a)
        response = client.delete('/api/favorites/99999/')
        assert response.status_code == 404


# =============================================================================
# Collections API Tests
# =============================================================================

@pytest.mark.django_db
class TestCollectionsAPI:
    """Tests for collections endpoints."""

    def test_list_collections_empty(self, client, profile_a):
        """List collections returns empty list for new profile."""
        select_profile(client, profile_a)
        response = client.get('/api/collections/')
        assert response.status_code == 200
        assert response.json() == []

    def test_create_collection(self, client, profile_a):
        """Create a new collection."""
        select_profile(client, profile_a)
        response = client.post(
            '/api/collections/',
            {'name': 'Desserts', 'description': 'My favorite desserts'},
            content_type='application/json',
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'Desserts'
        assert data['description'] == 'My favorite desserts'
        assert data['recipe_count'] == 0

    def test_create_collection_duplicate_name(self, client, profile_a):
        """Creating collection with duplicate name returns error."""
        select_profile(client, profile_a)
        RecipeCollection.objects.create(profile=profile_a, name='Desserts')

        response = client.post(
            '/api/collections/',
            {'name': 'Desserts'},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'already exists' in response.json()['detail']

    def test_get_collection(self, client, profile_a, recipe):
        """Get a collection with its recipes."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )
        RecipeCollectionItem.objects.create(collection=collection, recipe=recipe)

        response = client.get(f'/api/collections/{collection.id}/')
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Desserts'
        assert len(data['recipes']) == 1
        assert data['recipes'][0]['recipe']['id'] == recipe.id

    def test_update_collection(self, client, profile_a):
        """Update a collection."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )

        response = client.put(
            f'/api/collections/{collection.id}/',
            {'name': 'Sweets', 'description': 'Updated description'},
            content_type='application/json',
        )
        assert response.status_code == 200
        data = response.json()
        assert data['name'] == 'Sweets'
        assert data['description'] == 'Updated description'

    def test_delete_collection(self, client, profile_a):
        """Delete a collection."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )

        response = client.delete(f'/api/collections/{collection.id}/')
        assert response.status_code == 204
        assert not RecipeCollection.objects.filter(id=collection.id).exists()

    def test_add_recipe_to_collection(self, client, profile_a, recipe):
        """Add a recipe to a collection."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )

        response = client.post(
            f'/api/collections/{collection.id}/recipes/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 201
        assert response.json()['recipe']['id'] == recipe.id

    def test_add_duplicate_recipe_to_collection(self, client, profile_a, recipe):
        """Adding same recipe twice to collection returns error."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )
        RecipeCollectionItem.objects.create(collection=collection, recipe=recipe)

        response = client.post(
            f'/api/collections/{collection.id}/recipes/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 400
        assert 'already in this collection' in response.json()['detail']

    def test_remove_recipe_from_collection(self, client, profile_a, recipe):
        """Remove a recipe from a collection."""
        select_profile(client, profile_a)
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='Desserts'
        )
        RecipeCollectionItem.objects.create(collection=collection, recipe=recipe)

        response = client.delete(
            f'/api/collections/{collection.id}/recipes/{recipe.id}/'
        )
        assert response.status_code == 204
        assert not RecipeCollectionItem.objects.filter(
            collection=collection, recipe=recipe
        ).exists()


# =============================================================================
# History API Tests
# =============================================================================

@pytest.mark.django_db
class TestHistoryAPI:
    """Tests for view history endpoints."""

    def test_list_history_empty(self, client, profile_a):
        """List history returns empty list for new profile."""
        select_profile(client, profile_a)
        response = client.get('/api/history/')
        assert response.status_code == 200
        assert response.json() == []

    def test_record_view(self, client, profile_a, recipe):
        """Record a recipe view."""
        select_profile(client, profile_a)
        response = client.post(
            '/api/history/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 201
        assert response.json()['recipe']['id'] == recipe.id

    def test_record_view_updates_timestamp(self, client, profile_a, recipe):
        """Recording same recipe updates timestamp, returns 200."""
        select_profile(client, profile_a)
        # First view
        client.post(
            '/api/history/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        # Second view
        response = client.post(
            '/api/history/',
            {'recipe_id': recipe.id},
            content_type='application/json',
        )
        assert response.status_code == 200
        # Should still only have one history entry
        assert RecipeViewHistory.objects.filter(
            profile=profile_a, recipe=recipe
        ).count() == 1

    def test_history_limit(self, client, profile_a, db):
        """History returns limited results."""
        select_profile(client, profile_a)
        # Create 10 recipes and view history
        for i in range(10):
            recipe = Recipe.objects.create(host='test.com', title=f'Recipe {i}')
            RecipeViewHistory.objects.create(profile=profile_a, recipe=recipe)

        response = client.get('/api/history/?limit=5')
        assert response.status_code == 200
        assert len(response.json()) == 5

    def test_clear_history(self, client, profile_a, recipe):
        """Clear all view history."""
        select_profile(client, profile_a)
        RecipeViewHistory.objects.create(profile=profile_a, recipe=recipe)

        response = client.delete('/api/history/')
        assert response.status_code == 204
        assert not RecipeViewHistory.objects.filter(profile=profile_a).exists()


# =============================================================================
# Profile Isolation Tests
# =============================================================================

@pytest.mark.django_db
class TestProfileIsolation:
    """Tests ensuring data is properly isolated between profiles."""

    def test_favorites_isolation(self, client, profile_a, profile_b, recipe):
        """Profile A's favorites are not visible to Profile B."""
        # Profile A favorites a recipe
        RecipeFavorite.objects.create(profile=profile_a, recipe=recipe)

        # Profile B should not see it
        select_profile(client, profile_b)
        response = client.get('/api/favorites/')
        assert response.status_code == 200
        assert response.json() == []

        # Profile A should see it
        select_profile(client, profile_a)
        response = client.get('/api/favorites/')
        assert len(response.json()) == 1

    def test_collections_isolation(self, client, profile_a, profile_b):
        """Profile A's collections are not visible to Profile B."""
        # Profile A creates a collection
        RecipeCollection.objects.create(profile=profile_a, name='My Collection')

        # Profile B should not see it
        select_profile(client, profile_b)
        response = client.get('/api/collections/')
        assert response.status_code == 200
        assert response.json() == []

        # Profile A should see it
        select_profile(client, profile_a)
        response = client.get('/api/collections/')
        assert len(response.json()) == 1

    def test_collection_access_isolation(self, client, profile_a, profile_b):
        """Profile B cannot access Profile A's collection by ID."""
        # Profile A creates a collection
        collection = RecipeCollection.objects.create(
            profile=profile_a, name='My Collection'
        )

        # Profile B should get 404 when accessing it
        select_profile(client, profile_b)
        response = client.get(f'/api/collections/{collection.id}/')
        assert response.status_code == 404

    def test_history_isolation(self, client, profile_a, profile_b, recipe):
        """Profile A's history is not visible to Profile B."""
        # Profile A views a recipe
        RecipeViewHistory.objects.create(profile=profile_a, recipe=recipe)

        # Profile B should not see it
        select_profile(client, profile_b)
        response = client.get('/api/history/')
        assert response.status_code == 200
        assert response.json() == []

        # Profile A should see it
        select_profile(client, profile_a)
        response = client.get('/api/history/')
        assert len(response.json()) == 1

    def test_same_collection_name_different_profiles(
        self, client, profile_a, profile_b
    ):
        """Different profiles can have collections with same name."""
        select_profile(client, profile_a)
        response = client.post(
            '/api/collections/',
            {'name': 'Desserts'},
            content_type='application/json',
        )
        assert response.status_code == 201

        select_profile(client, profile_b)
        response = client.post(
            '/api/collections/',
            {'name': 'Desserts'},
            content_type='application/json',
        )
        assert response.status_code == 201


# =============================================================================
# Remix Visibility Tests
# =============================================================================

@pytest.mark.django_db
class TestRemixVisibility:
    """Tests for remix recipe visibility."""

    def test_remix_visible_to_owner(self, client, profile_a):
        """Remixes are visible to the creating profile."""
        select_profile(client, profile_a)
        remix = Recipe.objects.create(
            host='cookie.local',
            title='My Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        response = client.get('/api/recipes/')
        assert response.status_code == 200
        titles = [r['title'] for r in response.json()]
        assert 'My Remix' in titles

    def test_remix_hidden_from_other_profiles(self, client, profile_a, profile_b):
        """Remixes are hidden from other profiles."""
        # Profile A creates a remix
        Recipe.objects.create(
            host='cookie.local',
            title='Profile A Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        # Profile B should not see it
        select_profile(client, profile_b)
        response = client.get('/api/recipes/')
        assert response.status_code == 200
        titles = [r['title'] for r in response.json()]
        assert 'Profile A Remix' not in titles

    def test_remix_hidden_when_no_profile(self, client, profile_a):
        """Remixes are hidden when no profile is selected."""
        Recipe.objects.create(
            host='cookie.local',
            title='Hidden Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        response = client.get('/api/recipes/')
        assert response.status_code == 200
        titles = [r['title'] for r in response.json()]
        assert 'Hidden Remix' not in titles

    def test_non_remix_visible_to_all(self, client, profile_a, profile_b, recipe):
        """Non-remix recipes are visible to all profiles."""
        # No profile selected - should see the test recipe
        response = client.get('/api/recipes/')
        assert response.status_code == 200
        recipe_ids = [r['id'] for r in response.json()]
        assert recipe.id in recipe_ids

        # Profile A - should see the test recipe
        select_profile(client, profile_a)
        response = client.get('/api/recipes/')
        recipe_ids = [r['id'] for r in response.json()]
        assert recipe.id in recipe_ids

        # Profile B - should see the test recipe
        select_profile(client, profile_b)
        response = client.get('/api/recipes/')
        recipe_ids = [r['id'] for r in response.json()]
        assert recipe.id in recipe_ids

    def test_get_remix_by_id_owner(self, client, profile_a):
        """Owner can get their remix by ID."""
        select_profile(client, profile_a)
        remix = Recipe.objects.create(
            host='cookie.local',
            title='My Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        response = client.get(f'/api/recipes/{remix.id}/')
        assert response.status_code == 200
        assert response.json()['title'] == 'My Remix'

    def test_get_remix_by_id_other_profile(self, client, profile_a, profile_b):
        """Other profiles get 404 when accessing remix by ID."""
        remix = Recipe.objects.create(
            host='cookie.local',
            title='Profile A Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        select_profile(client, profile_b)
        response = client.get(f'/api/recipes/{remix.id}/')
        assert response.status_code == 404

    def test_get_remix_by_id_no_profile(self, client, profile_a):
        """No profile selected gets 404 when accessing remix by ID."""
        remix = Recipe.objects.create(
            host='cookie.local',
            title='Hidden Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        response = client.get(f'/api/recipes/{remix.id}/')
        assert response.status_code == 404

    def test_delete_remix_owner(self, client, profile_a):
        """Owner can delete their remix."""
        select_profile(client, profile_a)
        remix = Recipe.objects.create(
            host='cookie.local',
            title='My Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        response = client.delete(f'/api/recipes/{remix.id}/')
        assert response.status_code == 204
        assert not Recipe.objects.filter(id=remix.id).exists()

    def test_delete_remix_other_profile(self, client, profile_a, profile_b):
        """Other profiles cannot delete someone else's remix."""
        remix = Recipe.objects.create(
            host='cookie.local',
            title='Profile A Remix',
            is_remix=True,
            remix_profile=profile_a,
        )

        select_profile(client, profile_b)
        response = client.delete(f'/api/recipes/{remix.id}/')
        assert response.status_code == 404
        assert Recipe.objects.filter(id=remix.id).exists()
