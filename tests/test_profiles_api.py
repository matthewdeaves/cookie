import pytest
from apps.profiles.models import Profile


@pytest.mark.django_db
class TestProfilesAPI:
    """Tests for the Profile API endpoints."""

    def test_list_profiles_empty(self, client):
        """List profiles returns empty list when no profiles exist."""
        response = client.get("/api/profiles/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_profile(self, client):
        """Create a new profile."""
        data = {"name": "Test User", "avatar_color": "#d97850"}
        response = client.post(
            "/api/profiles/",
            data=data,
            content_type="application/json",
        )
        assert response.status_code == 201
        result = response.json()
        assert result["name"] == "Test User"
        assert result["avatar_color"] == "#d97850"
        assert result["theme"] == "light"
        assert result["unit_preference"] == "metric"

    def test_get_profile(self, client):
        """Get a profile by ID."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        response = client.get(f"/api/profiles/{profile.id}/")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_update_profile(self, client):
        """Update an existing profile."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        data = {
            "name": "Updated",
            "avatar_color": "#654321",
            "theme": "dark",
            "unit_preference": "imperial",
        }
        response = client.put(
            f"/api/profiles/{profile.id}/",
            data=data,
            content_type="application/json",
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated"
        assert result["theme"] == "dark"

    def test_delete_profile(self, client):
        """Delete a profile."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        response = client.delete(f"/api/profiles/{profile.id}/")
        assert response.status_code == 204
        assert not Profile.objects.filter(id=profile.id).exists()

    def test_select_profile(self, client):
        """Select a profile sets it in session."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        response = client.post(f"/api/profiles/{profile.id}/select/")
        assert response.status_code == 200
        assert client.session.get("profile_id") == profile.id
