"""
AI settings and prompts API endpoints.
"""

from typing import List, Optional

from ninja import Router, Schema

from apps.core.models import AppSettings

from .models import AIPrompt
from .services.openrouter import OpenRouterService, AIUnavailableError

router = Router(tags=['ai'])


# Schemas

class AIStatusOut(Schema):
    available: bool
    default_model: str


class TestApiKeyIn(Schema):
    api_key: str


class TestApiKeyOut(Schema):
    success: bool
    message: str


class SaveApiKeyIn(Schema):
    api_key: str


class SaveApiKeyOut(Schema):
    success: bool
    message: str


class PromptOut(Schema):
    prompt_type: str
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    model: str
    is_active: bool


class PromptUpdateIn(Schema):
    system_prompt: Optional[str] = None
    user_prompt_template: Optional[str] = None
    model: Optional[str] = None
    is_active: Optional[bool] = None


class ModelOut(Schema):
    id: str
    name: str


class ErrorOut(Schema):
    error: str
    message: str


# Endpoints

@router.get('/status', response=AIStatusOut)
def get_ai_status(request):
    """Check if AI service is available."""
    settings = AppSettings.get()
    return {
        'available': bool(settings.openrouter_api_key),
        'default_model': settings.default_ai_model,
    }


@router.post('/test-api-key', response={200: TestApiKeyOut, 400: ErrorOut})
def test_api_key(request, data: TestApiKeyIn):
    """Test if an API key is valid."""
    if not data.api_key:
        return 400, {
            'error': 'validation_error',
            'message': 'API key is required',
        }

    success, message = OpenRouterService.test_connection(data.api_key)
    return {
        'success': success,
        'message': message,
    }


@router.post('/save-api-key', response={200: SaveApiKeyOut, 400: ErrorOut})
def save_api_key(request, data: SaveApiKeyIn):
    """Save the OpenRouter API key."""
    settings = AppSettings.get()
    settings.openrouter_api_key = data.api_key
    settings.save()

    return {
        'success': True,
        'message': 'API key saved successfully',
    }


@router.get('/prompts', response=List[PromptOut])
def list_prompts(request):
    """List all AI prompts."""
    prompts = AIPrompt.objects.all()
    return list(prompts)


@router.get('/prompts/{prompt_type}', response={200: PromptOut, 404: ErrorOut})
def get_prompt(request, prompt_type: str):
    """Get a specific AI prompt by type."""
    try:
        prompt = AIPrompt.objects.get(prompt_type=prompt_type)
        return prompt
    except AIPrompt.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Prompt type "{prompt_type}" not found',
        }


@router.put('/prompts/{prompt_type}', response={200: PromptOut, 404: ErrorOut})
def update_prompt(request, prompt_type: str, data: PromptUpdateIn):
    """Update a specific AI prompt."""
    try:
        prompt = AIPrompt.objects.get(prompt_type=prompt_type)
    except AIPrompt.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Prompt type "{prompt_type}" not found',
        }

    # Update only provided fields
    if data.system_prompt is not None:
        prompt.system_prompt = data.system_prompt
    if data.user_prompt_template is not None:
        prompt.user_prompt_template = data.user_prompt_template
    if data.model is not None:
        prompt.model = data.model
    if data.is_active is not None:
        prompt.is_active = data.is_active

    prompt.save()
    return prompt


@router.get('/models', response=List[ModelOut])
def list_models(request):
    """List available AI models."""
    return [
        {'id': model_id, 'name': model_name}
        for model_id, model_name in AIPrompt.AVAILABLE_MODELS
    ]
