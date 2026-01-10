"""System API for administrative operations like database reset."""

import os
import shutil

from django.conf import settings
from django.core.cache import cache
from django.core.management import call_command
from django.contrib.sessions.models import Session
from ninja import Router, Schema

from apps.profiles.models import Profile
from apps.recipes.models import (
    Recipe,
    RecipeFavorite,
    RecipeCollection,
    RecipeCollectionItem,
    RecipeViewHistory,
    SearchSource,
    ServingAdjustment,
    CachedSearchImage,
)
from apps.ai.models import AIDiscoverySuggestion, AIPrompt

router = Router(tags=['system'])


class HealthSchema(Schema):
    status: str
    database: str


@router.get('/health/', response=HealthSchema)
def health_check(request):
    """Simple health check for container orchestration."""
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        return {'status': 'healthy', 'database': 'ok'}
    except Exception:
        return {'status': 'unhealthy', 'database': 'error'}


class DataCountsSchema(Schema):
    profiles: int
    recipes: int
    recipe_images: int
    favorites: int
    collections: int
    collection_items: int
    view_history: int
    ai_suggestions: int
    serving_adjustments: int
    cached_search_images: int


class ResetPreviewSchema(Schema):
    data_counts: DataCountsSchema
    preserved: list[str]
    warnings: list[str]


class ResetConfirmSchema(Schema):
    confirmation_text: str  # Must be "RESET"


class ErrorSchema(Schema):
    error: str
    message: str


class ResetSuccessSchema(Schema):
    success: bool
    message: str
    actions_performed: list[str]


@router.get('/reset-preview/', response=ResetPreviewSchema)
def get_reset_preview(request):
    """Get summary of data that will be deleted on reset."""
    return {
        'data_counts': {
            'profiles': Profile.objects.count(),
            'recipes': Recipe.objects.count(),
            'recipe_images': Recipe.objects.exclude(image='').exclude(
                image__isnull=True
            ).count(),
            'favorites': RecipeFavorite.objects.count(),
            'collections': RecipeCollection.objects.count(),
            'collection_items': RecipeCollectionItem.objects.count(),
            'view_history': RecipeViewHistory.objects.count(),
            'ai_suggestions': AIDiscoverySuggestion.objects.count(),
            'serving_adjustments': ServingAdjustment.objects.count(),
            'cached_search_images': CachedSearchImage.objects.count(),
        },
        'preserved': [
            'Search source configurations',
            'AI prompt templates',
            'Application settings',
        ],
        'warnings': [
            'All user data will be permanently deleted',
            'All recipe images will be removed from storage',
            'This action cannot be undone',
        ],
    }


@router.post('/reset/', response={200: ResetSuccessSchema, 400: ErrorSchema})
def reset_database(request, data: ResetConfirmSchema):
    """
    Completely reset the database to factory state.

    Requires confirmation_text="RESET" to proceed.
    """
    if data.confirmation_text != 'RESET':
        return 400, {
            'error': 'invalid_confirmation',
            'message': 'Type RESET to confirm',
        }

    try:
        # 1. Clear database tables (order matters for FK constraints)
        # Start with leaf tables that depend on others
        AIDiscoverySuggestion.objects.all().delete()
        ServingAdjustment.objects.all().delete()
        RecipeViewHistory.objects.all().delete()
        RecipeCollectionItem.objects.all().delete()
        RecipeCollection.objects.all().delete()
        RecipeFavorite.objects.all().delete()
        CachedSearchImage.objects.all().delete()

        # Delete all recipes (this will cascade to related items)
        Recipe.objects.all().delete()

        # Delete all profiles
        Profile.objects.all().delete()

        # Reset SearchSource failure counters (keep selectors)
        SearchSource.objects.all().update(
            consecutive_failures=0,
            needs_attention=False,
            last_validated_at=None,
        )

        # 2. Clear recipe images
        images_dir = os.path.join(settings.MEDIA_ROOT, 'recipe_images')
        if os.path.exists(images_dir):
            shutil.rmtree(images_dir)
            os.makedirs(images_dir)  # Recreate empty directory

        # Clear cached search images
        search_images_dir = os.path.join(settings.MEDIA_ROOT, 'search_images')
        if os.path.exists(search_images_dir):
            shutil.rmtree(search_images_dir)
            os.makedirs(search_images_dir)  # Recreate empty directory

        # 3. Clear Django cache
        cache.clear()

        # 4. Clear all sessions
        Session.objects.all().delete()

        # 5. Re-run migrations (ensures clean state)
        call_command('migrate', verbosity=0)

        # 6. Re-seed default data
        try:
            call_command('seed_search_sources', verbosity=0)
        except Exception:
            pass  # Command may not exist yet

        try:
            call_command('seed_ai_prompts', verbosity=0)
        except Exception:
            pass  # Command may not exist yet

        return {
            'success': True,
            'message': 'Database reset complete',
            'actions_performed': [
                'Deleted all user profiles',
                'Deleted all recipes and images',
                'Cleared all favorites and collections',
                'Cleared all view history',
                'Cleared all AI cache data',
                'Cleared all cached search images',
                'Reset search source counters',
                'Cleared application cache',
                'Cleared all sessions',
                'Re-ran database migrations',
                'Restored default seed data',
            ],
        }

    except Exception as e:
        return 400, {'error': 'reset_failed', 'message': str(e)}
