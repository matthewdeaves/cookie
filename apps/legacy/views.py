"""Views for legacy frontend."""

from django.shortcuts import render, redirect, get_object_or_404

from apps.core.models import AppSettings
from apps.profiles.models import Profile
from apps.ai.models import AIPrompt
from apps.ai.services.openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from apps.recipes.models import (
    Recipe,
    RecipeCollection,
    RecipeFavorite,
    RecipeViewHistory,
)


def profile_selector(request):
    """Profile selector screen."""
    profiles = list(Profile.objects.all().values(
        'id', 'name', 'avatar_color', 'theme', 'unit_preference'
    ))
    return render(request, 'legacy/profile_selector.html', {
        'profiles': profiles,
    })


def home(request):
    """Home screen."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get favorites for this profile
    favorites_qs = RecipeFavorite.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-created_at')
    favorites_count = favorites_qs.count()
    favorites = favorites_qs[:12]

    # Get recently viewed for this profile
    history_qs = RecipeViewHistory.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-viewed_at')
    history_count = history_qs.count()
    history = history_qs[:6]

    # Build favorite recipe IDs set for checking
    favorite_recipe_ids = set(f.recipe_id for f in favorites)

    return render(request, 'legacy/home.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'favorites': favorites,
        'favorites_count': favorites_count,
        'history': history,
        'history_count': history_count,
        'favorite_recipe_ids': favorite_recipe_ids,
    })


def search(request):
    """Search results screen."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    query = request.GET.get('q', '')
    # Detect if query is a URL
    is_url = query.strip().startswith('http://') or query.strip().startswith('https://')

    return render(request, 'legacy/search.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'query': query,
        'is_url': is_url,
    })


def recipe_detail(request, recipe_id):
    """Recipe detail screen."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get the recipe
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check remix visibility
    if recipe.is_remix and recipe.remix_profile_id != profile.id:
        return redirect('legacy:home')

    # Record view history
    RecipeViewHistory.objects.update_or_create(
        profile=profile,
        recipe=recipe,
        defaults={},  # Just update viewed_at (auto_now)
    )

    # Check if recipe is favorited
    is_favorite = RecipeFavorite.objects.filter(
        profile=profile,
        recipe=recipe,
    ).exists()

    # Get user's collections for the "add to collection" feature
    collections = RecipeCollection.objects.filter(profile=profile)

    # Get app settings to check AI availability
    settings = AppSettings.get()
    ai_available = bool(settings.openrouter_api_key)

    # Prepare ingredient groups or flat list
    has_ingredient_groups = bool(recipe.ingredient_groups)

    # Prepare instructions
    instructions = recipe.instructions
    if not instructions and recipe.instructions_text:
        instructions = [s.strip() for s in recipe.instructions_text.split('\n') if s.strip()]

    return render(request, 'legacy/recipe_detail.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'recipe': recipe,
        'is_favorite': is_favorite,
        'collections': collections,
        'ai_available': ai_available,
        'has_ingredient_groups': has_ingredient_groups,
        'instructions': instructions,
    })


def play_mode(request, recipe_id):
    """Play mode / cooking mode screen."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get the recipe
    recipe = get_object_or_404(Recipe, id=recipe_id)

    # Check remix visibility
    if recipe.is_remix and recipe.remix_profile_id != profile.id:
        return redirect('legacy:home')

    # Prepare instructions
    instructions = recipe.instructions
    if not instructions and recipe.instructions_text:
        instructions = [s.strip() for s in recipe.instructions_text.split('\n') if s.strip()]

    return render(request, 'legacy/play_mode.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'recipe': recipe,
        'instructions': instructions,
        'instructions_json': instructions,  # For JavaScript
    })


def all_recipes(request):
    """All Recipes screen - shows all viewed recipes (history)."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get all history for this profile (no limit)
    history = RecipeViewHistory.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-viewed_at')

    # Build set of favorite recipe IDs for display
    favorite_recipe_ids = set(
        RecipeFavorite.objects.filter(profile=profile).values_list('recipe_id', flat=True)
    )

    return render(request, 'legacy/all_recipes.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'history': history,
        'favorite_recipe_ids': favorite_recipe_ids,
    })


def favorites(request):
    """Favorites screen - shows all favorited recipes."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get all favorites for this profile
    favorites = RecipeFavorite.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-created_at')

    return render(request, 'legacy/favorites.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'favorites': favorites,
    })


def collections(request):
    """Collections list screen."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get all collections for this profile
    collections = RecipeCollection.objects.filter(
        profile=profile
    ).prefetch_related('items__recipe').order_by('-updated_at')

    return render(request, 'legacy/collections.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'collections': collections,
    })


def collection_detail(request, collection_id):
    """Collection detail screen - shows recipes in a collection."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get the collection (must belong to this profile)
    collection = get_object_or_404(
        RecipeCollection, id=collection_id, profile=profile
    )

    # Get all items in this collection
    items = collection.items.select_related('recipe').order_by('order', '-added_at')

    # Build set of favorite recipe IDs for display
    favorite_recipe_ids = set(
        RecipeFavorite.objects.filter(profile=profile).values_list('recipe_id', flat=True)
    )

    return render(request, 'legacy/collection_detail.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'collection': collection,
        'items': items,
        'favorite_recipe_ids': favorite_recipe_ids,
    })


def settings(request):
    """Settings screen - AI prompts configuration."""
    profile_id = request.session.get('profile_id')
    if not profile_id:
        return redirect('legacy:profile_selector')

    try:
        profile = Profile.objects.get(id=profile_id)
    except Profile.DoesNotExist:
        del request.session['profile_id']
        return redirect('legacy:profile_selector')

    # Get app settings
    app_settings = AppSettings.get()
    ai_available = bool(app_settings.openrouter_api_key)

    # Get all AI prompts
    prompts = list(AIPrompt.objects.all().order_by('name'))

    # Get available models from OpenRouter
    try:
        service = OpenRouterService()
        models = service.get_available_models()
    except (AIUnavailableError, AIResponseError):
        models = []

    return render(request, 'legacy/settings.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'ai_available': ai_available,
        'default_model': app_settings.default_ai_model,
        'prompts': prompts,
        'models': models,
    })
