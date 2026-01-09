"""
AI settings and prompts API endpoints.
"""

from typing import List, Optional

from ninja import Router, Schema

from apps.core.models import AppSettings
from apps.profiles.models import Profile
from apps.recipes.models import Recipe

from .models import AIPrompt
from .services.openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .services.remix import get_remix_suggestions, create_remix
from .services.scaling import scale_recipe, calculate_nutrition
from .services.tips import generate_tips, clear_tips
from .services.discover import get_discover_suggestions
from .services.validator import ValidationError

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


@router.put('/prompts/{prompt_type}', response={200: PromptOut, 404: ErrorOut, 422: ErrorOut})
def update_prompt(request, prompt_type: str, data: PromptUpdateIn):
    """Update a specific AI prompt."""
    try:
        prompt = AIPrompt.objects.get(prompt_type=prompt_type)
    except AIPrompt.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Prompt type "{prompt_type}" not found',
        }

    # Validate model if provided
    if data.model is not None:
        try:
            service = OpenRouterService()
            available_models = service.get_available_models()
            valid_model_ids = {m['id'] for m in available_models}

            if data.model not in valid_model_ids:
                return 422, {
                    'error': 'invalid_model',
                    'message': f'Model "{data.model}" is not available. Please select a valid model.',
                }
        except AIUnavailableError:
            # If we can't validate (no API key), allow the change but it may fail later
            pass
        except AIResponseError:
            # If model list fetch fails, allow the change but it may fail later
            pass

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
    """List available AI models from OpenRouter."""
    try:
        service = OpenRouterService()
        return service.get_available_models()
    except AIUnavailableError:
        # No API key configured - return empty list
        return []
    except AIResponseError:
        # API error - return empty list
        return []


# Remix Schemas

class RemixSuggestionsIn(Schema):
    recipe_id: int


class RemixSuggestionsOut(Schema):
    suggestions: List[str]


class CreateRemixIn(Schema):
    recipe_id: int
    modification: str
    profile_id: int


class RemixOut(Schema):
    id: int
    title: str
    description: str
    ingredients: List[str]
    instructions: List[str]
    host: str
    site_name: str
    is_remix: bool
    prep_time: Optional[int] = None
    cook_time: Optional[int] = None
    total_time: Optional[int] = None
    yields: str = ''
    servings: Optional[int] = None


# Remix Endpoints

@router.post('/remix-suggestions', response={200: RemixSuggestionsOut, 400: ErrorOut, 404: ErrorOut, 503: ErrorOut})
def remix_suggestions(request, data: RemixSuggestionsIn):
    """Get 6 AI-generated remix suggestions for a recipe.

    Only works for recipes owned by the requesting profile.
    """
    from apps.profiles.utils import get_current_profile_or_none
    profile = get_current_profile_or_none(request)

    try:
        # Verify recipe ownership
        recipe = Recipe.objects.get(id=data.recipe_id)
        if not profile or recipe.profile_id != profile.id:
            return 404, {
                'error': 'not_found',
                'message': f'Recipe {data.recipe_id} not found',
            }

        suggestions = get_remix_suggestions(data.recipe_id)
        return {'suggestions': suggestions}
    except Recipe.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Recipe {data.recipe_id} not found',
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e),
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


@router.post('/remix', response={200: RemixOut, 400: ErrorOut, 404: ErrorOut, 503: ErrorOut})
def create_remix_endpoint(request, data: CreateRemixIn):
    """Create a remixed recipe using AI.

    Only works for recipes owned by the requesting profile.
    The remix will be owned by the same profile.
    """
    from apps.profiles.utils import get_current_profile_or_none
    profile = get_current_profile_or_none(request)

    if not profile:
        return 404, {
            'error': 'not_found',
            'message': 'Profile not found',
        }

    # Verify the profile_id in the request matches the session profile
    if data.profile_id != profile.id:
        return 404, {
            'error': 'not_found',
            'message': f'Profile {data.profile_id} not found',
        }

    try:
        # Verify recipe ownership
        recipe = Recipe.objects.get(id=data.recipe_id)
        if recipe.profile_id != profile.id:
            return 404, {
                'error': 'not_found',
                'message': f'Recipe {data.recipe_id} not found',
            }

        remix = create_remix(
            recipe_id=data.recipe_id,
            modification=data.modification,
            profile=profile,
        )
        return {
            'id': remix.id,
            'title': remix.title,
            'description': remix.description,
            'ingredients': remix.ingredients,
            'instructions': remix.instructions,
            'host': remix.host,
            'site_name': remix.site_name,
            'is_remix': remix.is_remix,
            'prep_time': remix.prep_time,
            'cook_time': remix.cook_time,
            'total_time': remix.total_time,
            'yields': remix.yields,
            'servings': remix.servings,
        }
    except Recipe.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Recipe {data.recipe_id} not found',
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e),
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


# Scaling Schemas

class ScaleIn(Schema):
    recipe_id: int
    target_servings: int
    unit_system: str = 'metric'
    profile_id: int


class NutritionOut(Schema):
    per_serving: dict
    total: dict


class ScaleOut(Schema):
    target_servings: int
    original_servings: int
    ingredients: List[str]
    instructions: List[str] = []  # QA-031
    notes: List[str]
    prep_time_adjusted: Optional[int] = None  # QA-032
    cook_time_adjusted: Optional[int] = None  # QA-032
    total_time_adjusted: Optional[int] = None  # QA-032
    nutrition: Optional[NutritionOut] = None
    cached: bool


# Scaling Endpoints

@router.post('/scale', response={200: ScaleOut, 400: ErrorOut, 404: ErrorOut, 503: ErrorOut})
def scale_recipe_endpoint(request, data: ScaleIn):
    """Scale a recipe to a different number of servings.

    Only works for recipes owned by the requesting profile.
    """
    from apps.profiles.utils import get_current_profile_or_none
    profile = get_current_profile_or_none(request)

    if not profile:
        return 404, {
            'error': 'not_found',
            'message': 'Profile not found',
        }

    # Verify the profile_id in the request matches the session profile
    if data.profile_id != profile.id:
        return 404, {
            'error': 'not_found',
            'message': f'Profile {data.profile_id} not found',
        }

    try:
        recipe = Recipe.objects.get(id=data.recipe_id)
        # Verify recipe ownership
        if recipe.profile_id != profile.id:
            return 404, {
                'error': 'not_found',
                'message': f'Recipe {data.recipe_id} not found',
            }
    except Recipe.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Recipe {data.recipe_id} not found',
        }

    try:
        result = scale_recipe(
            recipe_id=data.recipe_id,
            target_servings=data.target_servings,
            profile=profile,
            unit_system=data.unit_system,
        )

        # Calculate nutrition if available
        nutrition = None
        if recipe.nutrition:
            nutrition = calculate_nutrition(
                recipe=recipe,
                original_servings=recipe.servings,
                target_servings=data.target_servings,
            )

        return {
            'target_servings': result['target_servings'],
            'original_servings': result['original_servings'],
            'ingredients': result['ingredients'],
            'instructions': result.get('instructions', []),  # QA-031
            'notes': result['notes'],
            'prep_time_adjusted': result.get('prep_time_adjusted'),  # QA-032
            'cook_time_adjusted': result.get('cook_time_adjusted'),  # QA-032
            'total_time_adjusted': result.get('total_time_adjusted'),  # QA-032
            'nutrition': nutrition,
            'cached': result['cached'],
        }
    except ValueError as e:
        return 400, {
            'error': 'validation_error',
            'message': str(e),
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e),
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


# Tips Schemas

class TipsIn(Schema):
    recipe_id: int
    regenerate: bool = False


class TipsOut(Schema):
    tips: List[str]
    cached: bool


# Tips Endpoints

@router.post('/tips', response={200: TipsOut, 400: ErrorOut, 404: ErrorOut, 503: ErrorOut})
def tips_endpoint(request, data: TipsIn):
    """Generate cooking tips for a recipe.

    Pass regenerate=True to clear existing tips and generate fresh ones.
    Only works for recipes owned by the requesting profile.
    """
    from apps.profiles.utils import get_current_profile_or_none
    profile = get_current_profile_or_none(request)

    try:
        # Verify recipe ownership
        recipe = Recipe.objects.get(id=data.recipe_id)
        if not profile or recipe.profile_id != profile.id:
            return 404, {
                'error': 'not_found',
                'message': f'Recipe {data.recipe_id} not found',
            }

        # Clear existing tips if regenerate requested
        if data.regenerate:
            clear_tips(data.recipe_id)

        result = generate_tips(data.recipe_id)
        return result
    except Recipe.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Recipe {data.recipe_id} not found',
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e),
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


# Discover Schemas

class DiscoverSuggestionOut(Schema):
    type: str
    title: str
    description: str
    search_query: str


class DiscoverOut(Schema):
    suggestions: List[DiscoverSuggestionOut]
    refreshed_at: str


# Discover Endpoints

@router.get('/discover/{profile_id}/', response={200: DiscoverOut, 404: ErrorOut, 503: ErrorOut})
def discover_endpoint(request, profile_id: int):
    """Get AI discovery suggestions for a profile.

    Returns cached suggestions if still valid (within 24 hours),
    otherwise generates new suggestions via AI.

    For new users (no favorites), only seasonal suggestions are returned.
    """
    try:
        result = get_discover_suggestions(profile_id)
        return result
    except Profile.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'Profile {profile_id} not found',
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e),
        }
