import json

import pytest
from django.contrib.auth.models import User

from apps.profiles.models import Profile
from apps.recipes.models import Recipe, RecipeCollection, RecipeFavorite, RecipeViewHistory


@pytest.mark.django_db
class TestProfilesAPI:
    """Tests for the Profile API endpoints."""

    def test_list_profiles_no_auth_in_home_mode(self, client):
        """List profiles is public in home mode (profile selection screen)."""
        response = client.get("/api/profiles/")
        assert response.status_code == 200

    def test_list_profiles(self, client):
        """List profiles returns profiles for authenticated user."""
        profile = Profile.objects.create(name="Test User", avatar_color="#d97850")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.get("/api/profiles/")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

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
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.get(f"/api/profiles/{profile.id}/")
        assert response.status_code == 200
        assert response.json()["name"] == "Test"

    def test_get_profile_requires_auth(self, client):
        """Get profile requires authentication."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        response = client.get(f"/api/profiles/{profile.id}/")
        assert response.status_code == 401

    def test_update_profile(self, client):
        """Update an existing profile."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
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
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.delete(f"/api/profiles/{profile.id}/")
        assert response.status_code == 204
        assert not Profile.objects.filter(id=profile.id).exists()

    def test_select_profile(self, client):
        """Select a profile sets it in session."""
        profile = Profile.objects.create(name="Test", avatar_color="#123456")
        response = client.post(f"/api/profiles/{profile.id}/select/")
        assert response.status_code == 200
        assert client.session.get("profile_id") == profile.id


# ── Helpers for passkey mode tests ──


def _create_user(username, is_staff=False):
    user = User.objects.create_user(
        username=username,
        password="!",
        email="",
        is_active=True,
        is_staff=is_staff,
    )
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login(client, user):
    client.force_login(user)
    session = client.session
    session["profile_id"] = user.profile.id
    session.save()


# ── GET /api/profiles/{id}/deletion-preview/ ──


@pytest.mark.django_db
class TestDeletionPreview:
    def test_empty_profile(self, client):
        """Preview for profile with no data shows all zero counts."""
        profile = Profile.objects.create(name="Empty", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.get(f"/api/profiles/{profile.id}/deletion-preview/")
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["name"] == "Empty"
        counts = data["data_to_delete"]
        assert counts["remixes"] == 0
        assert counts["favorites"] == 0
        assert counts["collections"] == 0
        assert counts["view_history"] == 0
        assert len(data["warnings"]) == 3

    def test_profile_with_data(self, client):
        """Preview counts remixes, favorites, collections, and history."""
        profile = Profile.objects.create(name="Active", avatar_color="#bbb")
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        # Create a regular recipe for favorites
        recipe = Recipe.objects.create(
            profile=profile,
            title="Regular",
            host="example.com",
            ingredients=["flour"],
            instructions=[{"text": "mix"}],
        )
        # Create a remix
        Recipe.objects.create(
            profile=profile,
            title="My Remix",
            host="user-generated",
            ingredients=["flour"],
            instructions=[{"text": "mix"}],
            is_remix=True,
            remix_profile=profile,
        )
        RecipeFavorite.objects.create(profile=profile, recipe=recipe)
        RecipeCollection.objects.create(profile=profile, name="Favorites")
        RecipeViewHistory.objects.create(profile=profile, recipe=recipe)

        response = client.get(f"/api/profiles/{profile.id}/deletion-preview/")
        assert response.status_code == 200
        counts = response.json()["data_to_delete"]
        assert counts["remixes"] == 1
        assert counts["favorites"] == 1
        assert counts["collections"] == 1
        assert counts["view_history"] == 1

    def test_nonexistent_profile(self, client):
        profile = Profile.objects.create(name="X", avatar_color="#ccc")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.get("/api/profiles/99999/deletion-preview/")
        assert response.status_code == 404

    def test_passkey_owner_can_view(self, client, settings):
        settings.AUTH_MODE = "passkey"
        user = _create_user("owner")
        _login(client, user)
        response = client.get(f"/api/profiles/{user.profile.id}/deletion-preview/")
        assert response.status_code == 200

    def test_passkey_non_owner_denied(self, client, settings):
        settings.AUTH_MODE = "passkey"
        owner = _create_user("owner")
        other = _create_user("other")
        _login(client, other)
        response = client.get(f"/api/profiles/{owner.profile.id}/deletion-preview/")
        assert response.status_code == 404

    def test_passkey_admin_can_view_any(self, client, settings):
        settings.AUTH_MODE = "passkey"
        admin = _create_user("admin", is_staff=True)
        regular = _create_user("regular")
        _login(client, admin)
        response = client.get(f"/api/profiles/{regular.profile.id}/deletion-preview/")
        assert response.status_code == 200


# ── POST /api/profiles/{id}/set-unlimited/ ──


@pytest.mark.django_db
class TestSetUnlimited:
    def test_grant_unlimited(self, client):
        """Set unlimited_ai to True."""
        profile = Profile.objects.create(name="User", avatar_color="#ddd")
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.post(
            f"/api/profiles/{profile.id}/set-unlimited/",
            data=json.dumps({"unlimited": True}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["unlimited_ai"] is True
        profile.refresh_from_db()
        assert profile.unlimited_ai is True

    def test_revoke_unlimited(self, client):
        """Set unlimited_ai back to False."""
        profile = Profile.objects.create(name="User", avatar_color="#ddd", unlimited_ai=True)
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.post(
            f"/api/profiles/{profile.id}/set-unlimited/",
            data=json.dumps({"unlimited": False}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["unlimited_ai"] is False
        profile.refresh_from_db()
        assert profile.unlimited_ai is False

    def test_nonexistent_profile(self, client):
        profile = Profile.objects.create(name="X", avatar_color="#eee")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.post(
            "/api/profiles/99999/set-unlimited/",
            data=json.dumps({"unlimited": True}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_passkey_non_admin_denied(self, client, settings):
        settings.AUTH_MODE = "passkey"
        regular = _create_user("regular")
        _login(client, regular)
        response = client.post(
            f"/api/profiles/{regular.profile.id}/set-unlimited/",
            data=json.dumps({"unlimited": True}),
            content_type="application/json",
        )
        assert response.status_code == 403


# ── PATCH /api/profiles/{id}/rename/ ──


@pytest.mark.django_db
class TestRenameProfile:
    def test_valid_rename(self, client):
        profile = Profile.objects.create(name="Old Name", avatar_color="#fff")
        session = client.session
        session["profile_id"] = profile.id
        session.save()

        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": "New Name"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "New Name"
        assert data["avatar_color"] == "#fff"
        profile.refresh_from_db()
        assert profile.name == "New Name"

    def test_empty_name(self, client):
        profile = Profile.objects.create(name="Test", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": ""}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_whitespace_only_name(self, client):
        profile = Profile.objects.create(name="Test", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_name_too_long(self, client):
        profile = Profile.objects.create(name="Test", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": "x" * 101}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_boundary_one_char(self, client):
        profile = Profile.objects.create(name="Test", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": "A"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        assert response.json()["name"] == "A"

    def test_boundary_100_chars(self, client):
        profile = Profile.objects.create(name="Test", avatar_color="#aaa")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            f"/api/profiles/{profile.id}/rename/",
            data=json.dumps({"name": "x" * 100}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_nonexistent_profile(self, client):
        profile = Profile.objects.create(name="X", avatar_color="#bbb")
        session = client.session
        session["profile_id"] = profile.id
        session.save()
        response = client.patch(
            "/api/profiles/99999/rename/",
            data=json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 404

    def test_passkey_non_admin_denied(self, client, settings):
        settings.AUTH_MODE = "passkey"
        regular = _create_user("regular")
        _login(client, regular)
        response = client.patch(
            f"/api/profiles/{regular.profile.id}/rename/",
            data=json.dumps({"name": "New"}),
            content_type="application/json",
        )
        assert response.status_code == 403


# ── DELETE /api/profiles/{id}/ (passkey self-deletion) ──


@pytest.mark.django_db
class TestPasskeySelfDeletion:
    def test_user_can_delete_own_account(self, client, settings):
        """Regular user can delete their own account in passkey mode."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("selfdelete")
        profile_id = user.profile.id
        user_id = user.id
        _login(client, user)

        response = client.delete(f"/api/profiles/{profile_id}/")
        assert response.status_code == 204
        assert not Profile.objects.filter(id=profile_id).exists()
        assert not User.objects.filter(id=user_id).exists()

    def test_user_cannot_delete_other_account(self, client, settings):
        """Regular user cannot delete another user's account."""
        settings.AUTH_MODE = "passkey"
        user_a = _create_user("user_a")
        user_b = _create_user("user_b")
        _login(client, user_a)

        response = client.delete(f"/api/profiles/{user_b.profile.id}/")
        assert response.status_code == 404
        assert Profile.objects.filter(id=user_b.profile.id).exists()
        assert User.objects.filter(id=user_b.id).exists()

    def test_admin_can_delete_any_account(self, client, settings):
        """Admin can delete any user's account."""
        settings.AUTH_MODE = "passkey"
        admin = _create_user("admin", is_staff=True)
        regular = _create_user("regular")
        regular_profile_id = regular.profile.id
        regular_user_id = regular.id
        _login(client, admin)

        response = client.delete(f"/api/profiles/{regular_profile_id}/")
        assert response.status_code == 204
        assert not Profile.objects.filter(id=regular_profile_id).exists()
        assert not User.objects.filter(id=regular_user_id).exists()

    def test_self_deletion_flushes_session(self, client, settings):
        """Deleting own account flushes the session."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("flushtest")
        _login(client, user)

        response = client.delete(f"/api/profiles/{user.profile.id}/")
        assert response.status_code == 204
        assert "profile_id" not in client.session

    def test_unauthenticated_cannot_delete(self, client, settings):
        """Unauthenticated request cannot delete any profile."""
        settings.AUTH_MODE = "passkey"
        user = _create_user("target")
        response = client.delete(f"/api/profiles/{user.profile.id}/")
        assert response.status_code == 401
        assert Profile.objects.filter(id=user.profile.id).exists()
