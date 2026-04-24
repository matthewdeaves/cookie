"""
AI settings and prompts API endpoints.
"""

import logging
from functools import wraps
from typing import Callable, List, Optional

from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema, Status

from apps.core.models import AppSettings
from apps.recipes.models import Recipe

from .models import AIPrompt
from .services.openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .services.tips import generate_tips, clear_tips
from .services.timer import generate_timer_name
from .services.selector import repair_selector, get_sources_needing_attention
from .services.validator import ValidationError
from .services.cache import is_ai_cache_hit
from .services.quota import release_quota, reserve_quota
from apps.core.auth import HomeOnlyAuth, SessionAuth

security_logger = logging.getLogger("security")

router = Router(tags=["ai"])


# Decorators


def handle_ai_errors(func: Callable) -> Callable:
    """Decorator to handle common AI service errors.

    Catches AIUnavailableError, AIResponseError, and ValidationError,
    returning appropriate error responses.

    Returns:
        - 503 with 'ai_unavailable' error for AIUnavailableError
        - 400 with 'ai_error' error for AIResponseError or ValidationError
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AIUnavailableError as e:
            return Status(
                503,
                {
                    "error": "ai_unavailable",
                    "message": str(e) or "AI features are not available. Please configure your API key in Settings.",
                    "action": "configure_key",
                },
            )
        except (AIResponseError, ValidationError) as e:
            return Status(
                400,
                {
                    "error": "ai_error",
                    "message": str(e),
                },
            )

    return wrapper


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


@router.get("/status", response=AIStatusOut, auth=SessionAuth())
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
        "available": False,
        "configured": has_key,
        "valid": False,
        "default_model": settings.default_ai_model,
        "error": None,
        "error_code": None,
    }

    if not has_key:
        status["error"] = "No API key configured"
        status["error_code"] = "no_api_key"
        return status

    # Validate key using cached validation
    is_valid, error_message = OpenRouterService.validate_key_cached()
    status["valid"] = is_valid
    status["available"] = is_valid

    if not is_valid:
        status["error"] = error_message or "API key is invalid or expired"
        status["error_code"] = "invalid_api_key"

    return status


@router.post("/test-api-key", response={200: TestApiKeyOut, 400: ErrorOut, 429: dict}, auth=HomeOnlyAuth())
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
def test_api_key(request, data: TestApiKeyIn):
    """Test if an API key is valid."""
    if getattr(request, "limited", False):
        return Status(429, {"detail": "Rate limit exceeded. Try again later."})
    if not data.api_key:
        return Status(
            400,
            {
                "error": "validation_error",
                "message": "API key is required",
            },
        )

    success, message = OpenRouterService.test_connection(data.api_key)
    return {
        "success": success,
        "message": message,
    }


@router.post("/save-api-key", response={200: SaveApiKeyOut, 400: ErrorOut, 429: dict}, auth=HomeOnlyAuth())
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
def save_api_key(request, data: SaveApiKeyIn):
    """Save the OpenRouter API key."""
    if getattr(request, "limited", False):
        return Status(429, {"detail": "Rate limit exceeded. Try again later."})
    settings = AppSettings.get()
    settings.openrouter_api_key = data.api_key
    settings.save()

    # Invalidate the validation cache since key was updated
    OpenRouterService.invalidate_key_cache()

    return {
        "success": True,
        "message": "API key saved successfully",
    }


@router.get("/prompts", response=List[PromptOut], auth=HomeOnlyAuth())
def list_prompts(request):
    """List all AI prompts."""
    prompts = AIPrompt.objects.all()
    return list(prompts)


def _get_prompt_or_error(prompt_type: str):
    """Return an AIPrompt or a (404, error dict) tuple."""
    try:
        return AIPrompt.objects.get(prompt_type=prompt_type)
    except AIPrompt.DoesNotExist:
        return Status(404, {"error": "not_found", "message": f'Prompt type "{prompt_type}" not found'})


def _validate_model(model_id: str):
    """Return a (422, error dict) tuple if model is invalid, else None."""
    try:
        valid_ids = {m["id"] for m in OpenRouterService().get_available_models()}
        if model_id not in valid_ids:
            return Status(
                422,
                {
                    "error": "invalid_model",
                    "message": f'Model "{model_id}" is not available. Please select a valid model.',
                },
            )
    except (AIUnavailableError, AIResponseError):
        # Can't validate — allow the change; it may fail later
        pass
    return None


@router.get("/prompts/{prompt_type}", response={200: PromptOut, 404: ErrorOut}, auth=HomeOnlyAuth())
def get_prompt(request, prompt_type: str):
    """Get a specific AI prompt by type."""
    return _get_prompt_or_error(prompt_type)


@router.put("/prompts/{prompt_type}", response={200: PromptOut, 404: ErrorOut, 422: ErrorOut}, auth=HomeOnlyAuth())
def update_prompt(request, prompt_type: str, data: PromptUpdateIn):
    """Update a specific AI prompt."""
    result = _get_prompt_or_error(prompt_type)
    if not isinstance(result, AIPrompt):
        return result
    prompt = result

    if data.model is not None:
        error = _validate_model(data.model)
        if error:
            return error

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


@router.get("/models", response=List[ModelOut], auth=SessionAuth())
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


# Tips Schemas


class TipsIn(Schema):
    recipe_id: int
    regenerate: bool = False


class TipsOut(Schema):
    tips: List[str]
    cached: bool


# Tips Endpoints


@router.post(
    "/tips", response={200: TipsOut, 400: ErrorOut, 404: ErrorOut, 429: dict, 503: ErrorOut}, auth=SessionAuth()
)
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
@handle_ai_errors
def tips_endpoint(request, data: TipsIn):
    """Generate cooking tips for a recipe.

    Pass regenerate=True to clear existing tips and generate fresh ones.
    Only works for recipes owned by the requesting profile.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/tips from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})

    allowed, info = reserve_quota(request.auth, "tips")
    if not allowed:
        return Status(429, {"error": "quota_exceeded", "message": "Daily limit reached for tips", **info})

    from apps.profiles.utils import get_current_profile_or_none

    profile = get_current_profile_or_none(request)

    try:
        recipe = Recipe.objects.get(id=data.recipe_id)
    except Recipe.DoesNotExist:
        release_quota(request.auth, "tips")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    if not profile or recipe.profile_id != profile.id:
        release_quota(request.auth, "tips")
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"Recipe {data.recipe_id} not found",
            },
        )

    # Clear existing tips if regenerate requested
    if data.regenerate:
        clear_tips(data.recipe_id)

    try:
        result = generate_tips(data.recipe_id)
    except Exception:
        release_quota(request.auth, "tips")
        raise
    if result.get("cached"):
        release_quota(request.auth, "tips")
    return result


# Timer Naming Schemas


class TimerNameIn(Schema):
    step_text: str
    duration_minutes: int


class TimerNameOut(Schema):
    label: str


# Timer Naming Endpoints


@router.post("/timer-name", response={200: TimerNameOut, 400: ErrorOut, 429: dict, 503: ErrorOut}, auth=SessionAuth())
@ratelimit(key="ip", rate="60/h", method="POST", block=False)
@handle_ai_errors
def timer_name_endpoint(request, data: TimerNameIn):
    """Generate a descriptive name for a cooking timer.

    Takes a cooking instruction and duration, returns a short label.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/timer-name from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})

    allowed, info = reserve_quota(request.auth, "timer")
    if not allowed:
        return Status(429, {"error": "quota_exceeded", "message": "Daily limit reached for timer", **info})

    step_text_clean = "".join(ch for ch in data.step_text if ch >= " " or ch in "\t\n\r").strip()
    if not step_text_clean:
        release_quota(request.auth, "timer")
        return Status(
            400,
            {
                "error": "validation_error",
                "message": "Step text is required",
            },
        )

    if data.duration_minutes <= 0:
        release_quota(request.auth, "timer")
        return Status(
            400,
            {
                "error": "validation_error",
                "message": "Duration must be positive",
            },
        )

    was_cached = is_ai_cache_hit("timer_name", step_text=step_text_clean, duration_minutes=data.duration_minutes)
    try:
        result = generate_timer_name(
            step_text=step_text_clean,
            duration_minutes=data.duration_minutes,
        )
    except Exception:
        release_quota(request.auth, "timer")
        raise
    if was_cached:
        release_quota(request.auth, "timer")
    return result


# Selector Repair Schemas


class SelectorRepairIn(Schema):
    source_id: int
    html_sample: str
    target: str = "recipe search result"
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


@router.post(
    "/repair-selector",
    response={200: SelectorRepairOut, 400: ErrorOut, 404: ErrorOut, 429: dict, 503: ErrorOut},
    auth=HomeOnlyAuth(),
)
@ratelimit(key="ip", rate="5/h", method="POST", block=False)
@handle_ai_errors
def repair_selector_endpoint(request, data: SelectorRepairIn):
    """Attempt to repair a broken CSS selector using AI.

    Analyzes HTML from the search page and suggests new selectors.
    If confidence is high enough and auto_update=True, the source is updated.

    This endpoint is intended for admin/maintenance use.
    """
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /ai/repair-selector from %s", request.META.get("REMOTE_ADDR"))
        return Status(429, {"error": "rate_limited", "message": "Too many requests. Please try again later."})
    from apps.recipes.models import SearchSource

    try:
        source = SearchSource.objects.get(id=data.source_id)
    except SearchSource.DoesNotExist:
        return Status(
            404,
            {
                "error": "not_found",
                "message": f"SearchSource {data.source_id} not found",
            },
        )

    if not data.html_sample:
        return Status(
            400,
            {
                "error": "validation_error",
                "message": "HTML sample is required",
            },
        )

    result = repair_selector(
        source=source,
        html_sample=data.html_sample,
        target=data.target,
        confidence_threshold=data.confidence_threshold,
        auto_update=data.auto_update,
    )
    return {
        "suggestions": result["suggestions"],
        "confidence": result["confidence"],
        "original_selector": result["original_selector"] or "",
        "updated": result["updated"],
        "new_selector": result.get("new_selector"),
    }


@router.get("/sources-needing-attention", response=List[SourceNeedingAttentionOut], auth=HomeOnlyAuth())
def sources_needing_attention_endpoint(request):
    """List all SearchSources that need attention (broken selectors).

    Returns sources with consecutive_failures >= 3 or needs_attention flag set.
    """
    sources = get_sources_needing_attention()
    return [
        {
            "id": s.id,
            "host": s.host,
            "name": s.name,
            "result_selector": s.result_selector or "",
            "consecutive_failures": s.consecutive_failures,
        }
        for s in sources
    ]
