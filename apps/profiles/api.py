import os
from datetime import datetime
from typing import List

from django.conf import settings
from django.db.models import Count, Q
from ninja import Router, Schema

from .models import Profile

router = Router(tags=['profiles'])


class ProfileIn(Schema):
    name: str
    avatar_color: str
    theme: str = 'light'
    unit_preference: str = 'metric'


class ProfileOut(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str


class ProfileStatsSchema(Schema):
    favorites: int
    collections: int
    collection_items: int
    remixes: int
    view_history: int
    scaling_cache: int
    discover_cache: int


class ProfileWithStatsSchema(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str
    created_at: datetime
    stats: ProfileStatsSchema


class DeletionDataSchema(Schema):
    remixes: int
    remix_images: int
    favorites: int
    collections: int
    collection_items: int
    view_history: int
    scaling_cache: int
    discover_cache: int


class ProfileSummarySchema(Schema):
    id: int
    name: str
    avatar_color: str
    created_at: datetime


class DeletionPreviewSchema(Schema):
    profile: ProfileSummarySchema
    data_to_delete: DeletionDataSchema
    warnings: List[str]


class ErrorSchema(Schema):
    error: str
    message: str


@router.get('/', response=List[ProfileWithStatsSchema])
def list_profiles(request):
    """List all profiles with stats for user management."""
    from apps.recipes.models import RecipeCollectionItem

    profiles = Profile.objects.annotate(
        favorites_count=Count('favorites', distinct=True),
        collections_count=Count('collections', distinct=True),
        remixes_count=Count(
            'remixes',
            filter=Q(remixes__is_remix=True),
            distinct=True
        ),
        view_history_count=Count('view_history', distinct=True),
        scaling_cache_count=Count('serving_adjustments', distinct=True),
        discover_cache_count=Count('ai_discovery_suggestions', distinct=True),
    ).order_by('-created_at')

    result = []
    for p in profiles:
        # Count collection items separately (requires join)
        collection_items_count = RecipeCollectionItem.objects.filter(
            collection__profile=p
        ).count()

        result.append(ProfileWithStatsSchema(
            id=p.id,
            name=p.name,
            avatar_color=p.avatar_color,
            theme=p.theme,
            unit_preference=p.unit_preference,
            created_at=p.created_at,
            stats=ProfileStatsSchema(
                favorites=p.favorites_count,
                collections=p.collections_count,
                collection_items=collection_items_count,
                remixes=p.remixes_count,
                view_history=p.view_history_count,
                scaling_cache=p.scaling_cache_count,
                discover_cache=p.discover_cache_count,
            )
        ))
    return result


@router.post('/', response={201: ProfileOut})
def create_profile(request, payload: ProfileIn):
    """Create a new profile."""
    profile = Profile.objects.create(**payload.dict())
    return 201, profile


@router.get('/{profile_id}/', response=ProfileOut)
def get_profile(request, profile_id: int):
    """Get a profile by ID."""
    return Profile.objects.get(id=profile_id)


@router.put('/{profile_id}/', response=ProfileOut)
def update_profile(request, profile_id: int, payload: ProfileIn):
    """Update a profile."""
    profile = Profile.objects.get(id=profile_id)
    for key, value in payload.dict().items():
        setattr(profile, key, value)
    profile.save()
    return profile


@router.get('/{profile_id}/deletion-preview/', response={200: DeletionPreviewSchema, 404: ErrorSchema})
def get_deletion_preview(request, profile_id: int):
    """Get summary of data that will be deleted with this profile."""
    from apps.ai.models import AIDiscoverySuggestion
    from apps.recipes.models import (
        Recipe,
        RecipeCollection,
        RecipeCollectionItem,
        RecipeFavorite,
        RecipeViewHistory,
        ServingAdjustment,
    )

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {'error': 'not_found', 'message': 'Profile not found'}

    # Count related data
    remixes = Recipe.objects.filter(is_remix=True, remix_profile=profile)
    favorites = RecipeFavorite.objects.filter(profile=profile)
    collections = RecipeCollection.objects.filter(profile=profile)
    collection_items = RecipeCollectionItem.objects.filter(collection__profile=profile)
    view_history = RecipeViewHistory.objects.filter(profile=profile)
    scaling_cache = ServingAdjustment.objects.filter(profile=profile)
    discover_cache = AIDiscoverySuggestion.objects.filter(profile=profile)

    # Count images that will be deleted
    remix_images_count = remixes.exclude(image='').exclude(image__isnull=True).count()

    return {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
            'created_at': profile.created_at,
        },
        'data_to_delete': {
            'remixes': remixes.count(),
            'remix_images': remix_images_count,
            'favorites': favorites.count(),
            'collections': collections.count(),
            'collection_items': collection_items.count(),
            'view_history': view_history.count(),
            'scaling_cache': scaling_cache.count(),
            'discover_cache': discover_cache.count(),
        },
        'warnings': [
            'All remixed recipes will be permanently deleted',
            'Recipe images for remixes will be removed from storage',
            'This action cannot be undone',
        ]
    }


@router.delete('/{profile_id}/', response={204: None, 400: ErrorSchema, 404: ErrorSchema})
def delete_profile(request, profile_id: int):
    """
    Delete a profile and ALL associated data.

    Cascade deletes:
    - Recipe remixes (is_remix=True, remix_profile=this)
    - Favorites
    - Collections and collection items
    - View history
    - Serving adjustment cache
    - AI discovery suggestions

    Manual cleanup:
    - Recipe images from deleted remixes
    """
    from apps.recipes.models import Recipe

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        return 404, {'error': 'not_found', 'message': 'Profile not found'}

    # Check if this is the current session profile
    current_profile_id = request.session.get('profile_id')
    if current_profile_id == profile_id:
        # Clear session profile
        del request.session['profile_id']

    # Collect image paths BEFORE cascade delete
    remix_images = list(
        Recipe.objects.filter(
            is_remix=True,
            remix_profile=profile,
            image__isnull=False
        ).exclude(image='').values_list('image', flat=True)
    )

    # Django CASCADE handles all related records
    profile.delete()

    # Clean up orphaned image files
    for image_path in remix_images:
        full_path = os.path.join(settings.MEDIA_ROOT, str(image_path))
        try:
            if os.path.exists(full_path):
                os.remove(full_path)
        except OSError:
            # Log but don't fail - orphaned files are non-critical
            pass

    return 204, None


@router.post('/{profile_id}/select/', response={200: ProfileOut})
def select_profile(request, profile_id: int):
    """Set a profile as the current profile (stored in session)."""
    profile = Profile.objects.get(id=profile_id)
    request.session['profile_id'] = profile.id
    return profile
