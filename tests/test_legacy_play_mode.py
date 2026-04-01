"""Tests for Legacy play mode view."""

import pytest

from apps.profiles.models import Profile
from apps.recipes.models import Recipe


@pytest.mark.django_db
class TestLegacyPlayMode:
    """Tests for the legacy play mode view."""

    def test_play_mode_redirects_without_profile(self, client):
        """Play mode redirects to profile selector when no profile in session."""
        profile = Profile.objects.create(name="Temp", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1", "Step 2"],
        )
        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        assert response.status_code == 302
        assert response.url == "/legacy/"

    def test_play_mode_renders(self, client):
        """Play mode renders successfully with profile."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Chocolate Chip Cookies",
            host="example.com",
            site_name="Example",
            instructions=["Mix ingredients", "Bake at 350F", "Cool and serve"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        assert response.status_code == 200
        content = response.content.decode()
        assert 'data-page="play-mode"' in content
        assert "Chocolate Chip Cookies" in content

    def test_play_mode_shows_first_instruction(self, client):
        """Play mode displays the first instruction on load."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["First step here", "Second step here"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "First step here" in content

    def test_play_mode_shows_step_counter(self, client):
        """Play mode shows step counter with total steps."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1", "Step 2", "Step 3"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        # Step counter shows "Step X of N" with total-steps span
        assert "play-step-counter" in content
        assert 'id="total-steps"' in content
        assert 'id="current-step"' in content

    def test_play_mode_shows_navigation_buttons(self, client):
        """Play mode shows previous/next buttons."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1", "Step 2"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "prev-btn" in content
        assert "next-btn" in content
        assert "Previous" in content
        assert "Next" in content

    def test_play_mode_shows_timer_panel(self, client):
        """Play mode includes timer panel."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Cook for 10 minutes"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "timer-panel" in content
        assert "Timers" in content

    def test_play_mode_shows_quick_timer_buttons(self, client):
        """Play mode shows quick timer buttons (+5, +10, +15 min)."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "5 min" in content
        assert "10 min" in content
        assert "15 min" in content

    def test_play_mode_shows_exit_button(self, client):
        """Play mode shows exit button linking back to recipe detail."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "exit-btn" in content
        assert f"/legacy/recipe/{recipe.id}/" in content

    def test_play_mode_empty_state(self, client):
        """Play mode shows empty state when no instructions."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=[],  # No instructions
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "No instructions available" in content

    def test_play_mode_uses_instructions_text_fallback(self, client):
        """Play mode falls back to instructions_text if instructions list is empty."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=[],
            instructions_text="Line one\nLine two\nLine three",
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "Line one" in content

    def test_play_mode_404_for_nonexistent(self, client):
        """Play mode returns 404 for non-existent recipe."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get("/legacy/recipe/99999/play/")
        assert response.status_code == 404

    def test_play_mode_hides_other_recipe(self, client):
        """Play mode returns 404 when trying to view another user's recipe."""
        profile1 = Profile.objects.create(name="User1", avatar_color="#d97850")
        profile2 = Profile.objects.create(name="User2", avatar_color="#6b8e5f")
        recipe = Recipe.objects.create(
            profile=profile2,
            title="Private Recipe",
            host="user-generated",
            site_name="User Generated",
            is_remix=True,
            remix_profile=profile2,
            instructions=["Step 1"],
        )
        client.post(f"/api/profiles/{profile1.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        assert response.status_code == 404  # Recipe not found for this profile

    def test_play_mode_includes_js(self, client):
        """Play mode includes required JavaScript files."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "timer.js" in content
        assert "time-detect.js" in content
        assert "pages/play.js" in content

    def test_play_mode_includes_css(self, client):
        """Play mode includes play-mode.css."""
        profile = Profile.objects.create(name="Test", avatar_color="#d97850")
        recipe = Recipe.objects.create(
            profile=profile,
            title="Test Recipe",
            host="example.com",
            site_name="Example",
            instructions=["Step 1"],
        )
        client.post(f"/api/profiles/{profile.id}/select/")

        response = client.get(f"/legacy/recipe/{recipe.id}/play/")
        content = response.content.decode()
        assert "play-mode.css" in content
