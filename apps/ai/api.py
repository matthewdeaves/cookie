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
from .services.timer import generate_timer_name
from .services.selector import repair_selector, get_sources_needing_attention
from .services.validator import ValidationError

router = Router(tags=['ai'])


# Schemas

class AIStatusOut(Schema):
    available: bool
    configured: bool
    valid: bool
    default_model: str
    error: Optional[str] = None
    error_code: Optional[str] = None


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
    action: Optional[str] = None  # User-facing action to resolve the error


# Endpoints

@router.get('/status', response=AIStatusOut)
def get_ai_status(request):
    """Check if AI service is available with optional key validation.

    Returns a status object with:
    - available: Whether AI features can be used (configured AND valid)
    - configured: Whether an API key is configured
    - valid: Whether the API key has been validated successfully
    - default_model: The default AI model
    - error: Error message if something is wrong
    - error_code: Machine-readable error code
    """
    settings = AppSettings.get()
    has_key = bool(settings.openrouter_api_key)

    status = {
        'available': False,
        'configured': has_key,
        'valid': False,
        'default_model': settings.default_ai_model,
        'error': None,
        'error_code': None,
    }

    if not has_key:
        status['error'] = 'No API key configured'
        status['error_code'] = 'no_api_key'
        return status

    # Validate key using cached validation
    is_valid, error_message = OpenRouterService.validate_key_cached()
    status['valid'] = is_valid
    status['available'] = is_valid

    if not is_valid:
        status['error'] = error_message or 'API key is invalid or expired'
        status['error_code'] = 'invalid_api_key'

    return status


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

    # Invalidate the validation cache since key was updated
    OpenRouterService.invalidate_key_cache()

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
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
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
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
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
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
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
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


# Timer Naming Schemas

class TimerNameIn(Schema):
    step_text: str
    duration_minutes: int


class TimerNameOut(Schema):
    label: str


# Timer Naming Endpoints

@router.post('/timer-name', response={200: TimerNameOut, 400: ErrorOut, 503: ErrorOut})
def timer_name_endpoint(request, data: TimerNameIn):
    """Generate a descriptive name for a cooking timer.

    Takes a cooking instruction and duration, returns a short label.
    """
    if not data.step_text:
        return 400, {
            'error': 'validation_error',
            'message': 'Step text is required',
        }

    if data.duration_minutes <= 0:
        return 400, {
            'error': 'validation_error',
            'message': 'Duration must be positive',
        }

    try:
        result = generate_timer_name(
            step_text=data.step_text,
            duration_minutes=data.duration_minutes,
        )
        return result
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
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
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
        }


# Selector Repair Schemas

class SelectorRepairIn(Schema):
    source_id: int
    html_sample: str
    target: str = 'recipe search result'
    confidence_threshold: float = 0.8
    auto_update: bool = True


class SelectorRepairOut(Schema):
    suggestions: List[str]
    confidence: float
    original_selector: str
    updated: bool
    new_selector: Optional[str] = None


class SourceNeedingAttentionOut(Schema):
    id: int
    host: str
    name: str
    result_selector: str
    consecutive_failures: int


# Selector Repair Endpoints

@router.post('/repair-selector', response={200: SelectorRepairOut, 400: ErrorOut, 404: ErrorOut, 503: ErrorOut})
def repair_selector_endpoint(request, data: SelectorRepairIn):
    """Attempt to repair a broken CSS selector using AI.

    Analyzes HTML from the search page and suggests new selectors.
    If confidence is high enough and auto_update=True, the source is updated.

    This endpoint is intended for admin/maintenance use.
    """
    from apps.recipes.models import SearchSource

    try:
        source = SearchSource.objects.get(id=data.source_id)
    except SearchSource.DoesNotExist:
        return 404, {
            'error': 'not_found',
            'message': f'SearchSource {data.source_id} not found',
        }

    if not data.html_sample:
        return 400, {
            'error': 'validation_error',
            'message': 'HTML sample is required',
        }

    try:
        result = repair_selector(
            source=source,
            html_sample=data.html_sample,
            target=data.target,
            confidence_threshold=data.confidence_threshold,
            auto_update=data.auto_update,
        )
        return {
            'suggestions': result['suggestions'],
            'confidence': result['confidence'],
            'original_selector': result['original_selector'] or '',
            'updated': result['updated'],
            'new_selector': result.get('new_selector'),
        }
    except AIUnavailableError as e:
        return 503, {
            'error': 'ai_unavailable',
            'message': str(e) or 'AI features are not available. Please configure your API key in Settings.',
            'action': 'configure_key',
        }
    except (AIResponseError, ValidationError) as e:
        return 400, {
            'error': 'ai_error',
            'message': str(e),
        }


@router.get('/sources-needing-attention', response=List[SourceNeedingAttentionOut])
def sources_needing_attention_endpoint(request):
    """List all SearchSources that need attention (broken selectors).

    Returns sources with consecutive_failures >= 3 or needs_attention flag set.
    """
    sources = get_sources_needing_attention()
    return [
        {
            'id': s.id,
            'host': s.host,
            'name': s.name,
            'result_selector': s.result_selector or '',
            'consecutive_failures': s.consecutive_failures,
        }
        for s in sources
    ]
