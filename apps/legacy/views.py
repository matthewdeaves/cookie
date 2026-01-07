"""Views for legacy frontend."""

from django.shortcuts import render, redirect

from apps.profiles.models import Profile


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

    return render(request, 'legacy/home.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
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
    return render(request, 'legacy/search.html', {
        'profile': {
            'id': profile.id,
            'name': profile.name,
            'avatar_color': profile.avatar_color,
        },
        'query': query,
    })
