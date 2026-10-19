"""Quota behaviour of /api/ai/scale when work fails after the AI has been called."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.core.cache import cache

from apps.ai.services.quota import get_usage
from apps.profiles.models import Profile
from apps.recipes.models import Recipe


@pytest.fixture(autouse=True)
def _clear_cache():
    cache.clear()


def _post_scale(client, profile, recipe):
    client.force_login(profile.user)
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client.post(
        "/api/ai/scale",
        data=json.dumps({"recipe_id": recipe.id, "target_servings": 8, "profile_id": profile.id}),
        content_type="application/json",
    )


@pytest.mark.django_db
@pytest.mark.parametrize(("cached", "expected_usage"), [(False, 1), (True, 0)])
def test_nutrition_failure_refunds_only_when_no_ai_call_was_made(client, settings, cached, expected_usage):
    settings.AUTH_MODE = "passkey"
    user = User.objects.create_user(username="scale_nutrition", password="!", email="", is_active=True)
    profile = Profile.objects.create(user=user, name="scale_nutrition", avatar_color="#d97850")
    recipe = Recipe.objects.create(
        profile=profile,
        title="Test Recipe",
        host="example.com",
        ingredients=["flour"],
        instructions=["mix"],
        servings=4,
        nutrition={"calories": "100"},
    )
    scaled = {"target_servings": 8, "original_servings": 4, "ingredients": ["2x flour"], "notes": [], "cached": cached}
    with (
        patch("apps.ai.api_scaling.scale_recipe", return_value=scaled),
        patch("apps.ai.api_scaling.calculate_nutrition", side_effect=RuntimeError("boom")),
        pytest.raises(RuntimeError, match="boom"),
    ):
        _post_scale(client, profile, recipe)
    assert get_usage(profile.pk)["scale"] == expected_usage
