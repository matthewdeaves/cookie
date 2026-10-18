"""Tests for the OpenRouter -> Anthropic model id and key migrations."""

import importlib

import pytest

core_mig = importlib.import_module("apps.core.migrations.0010_anthropic_api_key")
ai_mig = importlib.import_module("apps.ai.migrations.0012_anthropic_model_ids")


@pytest.mark.parametrize("mapper", [core_mig.to_anthropic_model_id, ai_mig.to_anthropic_model_id])
@pytest.mark.parametrize(
    "old,new",
    [
        ("anthropic/claude-haiku-4.5", "claude-haiku-5-5"),
        ("anthropic/claude-3.5-haiku", "claude-haiku-5-5"),
        ("anthropic/claude-sonnet-4", "claude-sonnet-5-5"),
        ("anthropic/claude-opus-4", "claude-opus-5-5"),
        ("anthropic/claude-opus-4.5", "claude-opus-5-5"),
        ("openai/gpt-4o", "claude-haiku-5-5"),
        ("google/gemini-2.5-pro-preview", "claude-haiku-5-5"),
        ("claude-sonnet-5-5", "claude-sonnet-5-5"),
        ("", "claude-haiku-5-5"),
    ],
)
def test_model_id_mapping(mapper, old, new):
    assert mapper(old) == new


@pytest.mark.django_db
def test_existing_prompts_use_anthropic_ids():
    from apps.ai.models import AIPrompt

    valid = {c[0] for c in AIPrompt.AVAILABLE_MODELS}
    assert AIPrompt.objects.exists()
    assert all(p.model in valid for p in AIPrompt.objects.all())
