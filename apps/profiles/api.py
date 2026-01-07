from typing import List

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


@router.get('/', response=List[ProfileOut])
def list_profiles(request):
    """List all profiles."""
    return Profile.objects.all()


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


@router.delete('/{profile_id}/', response={204: None})
def delete_profile(request, profile_id: int):
    """Delete a profile."""
    profile = Profile.objects.get(id=profile_id)
    profile.delete()
    return 204, None


@router.post('/{profile_id}/select/', response={200: ProfileOut})
def select_profile(request, profile_id: int):
    """Set a profile as the current profile (stored in session)."""
    profile = Profile.objects.get(id=profile_id)
    request.session['profile_id'] = profile.id
    return profile
