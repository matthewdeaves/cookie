"""Views for legacy frontend."""

from django.shortcuts import render, redirect

from apps.profiles.models import Profile
from apps.recipes.models import RecipeFavorite, RecipeViewHistory


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
    favorites = RecipeFavorite.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-created_at')[:12]

    # Get recently viewed for this profile
    history = RecipeViewHistory.objects.filter(
        profile=profile
    ).select_related('recipe').order_by('-viewed_at')[:6]

    # Build favorite recipe IDs set for checking
    favorite_recipe_ids = set(f.recipe_id for f in favorites)

    return render(request, 'legacy/home.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'favorites': favorites,
        'history': history,
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
