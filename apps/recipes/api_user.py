"""
User feature API endpoints: favorites, collections, history.

All endpoints are scoped to the current profile (from session).
"""

from typing import List, Optional

from django.db import IntegrityError
from django.db.models import Max
from django.shortcuts import get_object_or_404
from ninja import Router, Schema

from apps.profiles.utils import get_current_profile

from .api import RecipeListOut
from .models import (
    Recipe,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeFavorite,
    RecipeViewHistory,
)

# =============================================================================
# Favorites Router
# =============================================================================

favorites_router = Router(tags=['favorites'])


class FavoriteIn(Schema):
    recipe_id: int


class FavoriteOut(Schema):
    recipe: RecipeListOut
    created_at: str

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()


class ErrorOut(Schema):
    detail: str


@favorites_router.get('/', response=List[FavoriteOut])
def list_favorites(request):
    """List all favorites for the current profile."""
    profile = get_current_profile(request)
    return RecipeFavorite.objects.filter(profile=profile).select_related('recipe')


@favorites_router.post('/', response={201: FavoriteOut, 400: ErrorOut, 404: ErrorOut})
def add_favorite(request, payload: FavoriteIn):
    """Add a recipe to favorites."""
    profile = get_current_profile(request)
    recipe = get_object_or_404(Recipe, id=payload.recipe_id)

    try:
        favorite = RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        return 201, favorite
    except IntegrityError:
        return 400, {'detail': 'Recipe is already a favorite'}


@favorites_router.delete('/{recipe_id}/', response={204: None, 404: ErrorOut})
def remove_favorite(request, recipe_id: int):
    """Remove a recipe from favorites."""
    profile = get_current_profile(request)
    favorite = get_object_or_404(
        RecipeFavorite, profile=profile, recipe_id=recipe_id
    )
    favorite.delete()
    return 204, None


# =============================================================================
# Collections Router
# =============================================================================

collections_router = Router(tags=['collections'])


class CollectionIn(Schema):
    name: str
    description: str = ''


class CollectionItemIn(Schema):
    recipe_id: int


class CollectionItemOut(Schema):
    recipe: RecipeListOut
    order: int
    added_at: str

    @staticmethod
    def resolve_added_at(obj):
        return obj.added_at.isoformat()


class CollectionOut(Schema):
    id: int
    name: str
    description: str
    recipe_count: int
    created_at: str
    updated_at: str

    @staticmethod
    def resolve_recipe_count(obj):
        return obj.items.count()

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat()


class CollectionDetailOut(Schema):
    id: int
    name: str
    description: str
    recipes: List[CollectionItemOut]
    created_at: str
    updated_at: str

    @staticmethod
    def resolve_recipes(obj):
        return obj.items.select_related('recipe').all()

    @staticmethod
    def resolve_created_at(obj):
        return obj.created_at.isoformat()

    @staticmethod
    def resolve_updated_at(obj):
        return obj.updated_at.isoformat()


@collections_router.get('/', response=List[CollectionOut])
def list_collections(request):
    """List all collections for the current profile."""
    profile = get_current_profile(request)
    return RecipeCollection.objects.filter(profile=profile).prefetch_related('items')


@collections_router.post('/', response={201: CollectionOut, 400: ErrorOut})
def create_collection(request, payload: CollectionIn):
    """Create a new collection."""
    profile = get_current_profile(request)

    try:
        collection = RecipeCollection.objects.create(
            profile=profile,
            name=payload.name,
            description=payload.description,
        )
        return 201, collection
    except IntegrityError:
        return 400, {'detail': 'A collection with this name already exists'}


@collections_router.get('/{collection_id}/', response={200: CollectionDetailOut, 404: ErrorOut})
def get_collection(request, collection_id: int):
    """Get a collection with its recipes."""
    profile = get_current_profile(request)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )
    return collection


@collections_router.put('/{collection_id}/', response={200: CollectionOut, 400: ErrorOut, 404: ErrorOut})
def update_collection(request, collection_id: int, payload: CollectionIn):
    """Update a collection."""
    profile = get_current_profile(request)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )

    try:
        collection.name = payload.name
        collection.description = payload.description
        collection.save()
        return collection
    except IntegrityError:
        return 400, {'detail': 'A collection with this name already exists'}


@collections_router.delete('/{collection_id}/', response={204: None, 404: ErrorOut})
def delete_collection(request, collection_id: int):
    """Delete a collection."""
    profile = get_current_profile(request)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )
    collection.delete()
    return 204, None


@collections_router.post('/{collection_id}/recipes/', response={201: CollectionItemOut, 400: ErrorOut, 404: ErrorOut})
def add_recipe_to_collection(request, collection_id: int, payload: CollectionItemIn):
    """Add a recipe to a collection."""
    profile = get_current_profile(request)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )
    recipe = get_object_or_404(Recipe, id=payload.recipe_id)

    # Get the next order value
    max_order = collection.items.aggregate(max_order=Max('order'))['max_order']
    next_order = (max_order or 0) + 1

    try:
        item = RecipeCollectionItem.objects.create(
            collection=collection,
            recipe=recipe,
            order=next_order,
        )
        return 201, item
    except IntegrityError:
        return 400, {'detail': 'Recipe is already in this collection'}


@collections_router.delete('/{collection_id}/recipes/{recipe_id}/', response={204: None, 404: ErrorOut})
def remove_recipe_from_collection(request, collection_id: int, recipe_id: int):
    """Remove a recipe from a collection."""
    profile = get_current_profile(request)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )
    item = get_object_or_404(
        RecipeCollectionItem, collection=collection, recipe_id=recipe_id
    )
    item.delete()
    return 204, None


# =============================================================================
# History Router
# =============================================================================

history_router = Router(tags=['history'])


class HistoryIn(Schema):
    recipe_id: int


class HistoryOut(Schema):
    recipe: RecipeListOut
    viewed_at: str

    @staticmethod
    def resolve_viewed_at(obj):
        return obj.viewed_at.isoformat()


@history_router.get('/', response=List[HistoryOut])
def list_history(request, limit: int = 6):
    """
    Get recently viewed recipes for the current profile.

    Returns up to 6 most recent recipes by default.
    """
    profile = get_current_profile(request)
    return (
        RecipeViewHistory.objects.filter(profile=profile)
        .select_related('recipe')[:limit]
    )


@history_router.post('/', response={200: HistoryOut, 201: HistoryOut, 404: ErrorOut})
def record_view(request, payload: HistoryIn):
    """
    Record a recipe view.

    If the recipe was already viewed, updates the timestamp.
    """
    profile = get_current_profile(request)
    recipe = get_object_or_404(Recipe, id=payload.recipe_id)

    history, created = RecipeViewHistory.objects.update_or_create(
        profile=profile,
        recipe=recipe,
        defaults={},  # viewed_at auto-updates due to auto_now
    )

    status = 201 if created else 200
    return status, history


@history_router.delete('/', response={204: None})
def clear_history(request):
    """Clear all view history for the current profile."""
    profile = get_current_profile(request)
    RecipeViewHistory.objects.filter(profile=profile).delete()
    return 204, None
