"""AI discovery suggestions service."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List

from django.utils import timezone

from apps.profiles.models import Profile
from apps.recipes.models import RecipeFavorite, RecipeViewHistory

from ..models import AIPrompt, AIDiscoverySuggestion
from .openrouter import OpenRouterService, AIUnavailableError, AIResponseError
from .validator import AIResponseValidator, ValidationError

logger = logging.getLogger(__name__)

# Suggestions are cached for 24 hours
CACHE_DURATION_HOURS = 24


def get_discover_suggestions(profile_id: int) -> dict:
    """Get AI discovery suggestions for a profile.

    Returns cached suggestions if still valid (within 24 hours),
    otherwise generates new suggestions via AI.

    For new users (no favorites), only seasonal suggestions are returned.

    Args:
        profile_id: The ID of the profile to get suggestions for.

    Returns:
        Dict with suggestions array and refresh timestamp.

    Raises:
        Profile.DoesNotExist: If profile not found.
        AIUnavailableError: If AI service is not available.
    """
    profile = Profile.objects.get(id=profile_id)

    # Check for cached suggestions (within 24 hours)
    cache_cutoff = timezone.now() - timedelta(hours=CACHE_DURATION_HOURS)
    cached = AIDiscoverySuggestion.objects.filter(profile=profile, created_at__gte=cache_cutoff)

    if cached.exists():
        logger.info(f"Returning cached discover suggestions for profile {profile_id}")
        return _format_suggestions(cached)

    # Clear old suggestions
    AIDiscoverySuggestion.objects.filter(profile=profile).delete()

    # Check if user has viewing history
    has_history = RecipeViewHistory.objects.filter(profile=profile).exists()

    # Generate new suggestions
    suggestions = []

    # Always generate seasonal suggestions
    seasonal_suggestions = _generate_seasonal_suggestions(profile)
    suggestions.extend(seasonal_suggestions)

    # Only generate personalized suggestions if user has history
    if has_history:
        # Recommended based on what they've viewed
        recommended_suggestions = _generate_recommended_suggestions(profile)
        suggestions.extend(recommended_suggestions)

        # Try something new/different
        new_suggestions = _generate_new_suggestions(profile)
        suggestions.extend(new_suggestions)

    if not suggestions:
        # If no suggestions generated, return empty
        return {
            "suggestions": [],
            "refreshed_at": timezone.now().isoformat(),
        }

    return _format_suggestions(suggestions)


def _format_suggestions(suggestions) -> dict:
    """Format suggestions for API response."""
    result = []

    for suggestion in suggestions:
        result.append(
            {
                "type": suggestion.suggestion_type,
                "title": suggestion.title,
                "description": suggestion.description,
                "search_query": suggestion.search_query,
            }
        )

    # Get the most recent created_at for refreshed_at
    if hasattr(suggestions, "first"):
        # QuerySet
        first = suggestions.first()
        refreshed_at = first.created_at.isoformat() if first else timezone.now().isoformat()
    else:
        # List
        refreshed_at = suggestions[0].created_at.isoformat() if suggestions else timezone.now().isoformat()

    return {
        "suggestions": result,
        "refreshed_at": refreshed_at,
    }


def _generate_seasonal_suggestions(profile: Profile) -> List[AIDiscoverySuggestion]:
    """Generate seasonal/holiday suggestions."""
    try:
        prompt = AIPrompt.get_prompt("discover_seasonal")
    except AIPrompt.DoesNotExist:
        logger.warning("discover_seasonal prompt not found")
        return []

    # Get current date info
    now = datetime.now()
    date_str = now.strftime("%B %d, %Y")  # e.g., "January 15, 2024"
    season = _get_season(now)

    user_prompt = prompt.format_user_prompt(
        date=date_str,
        season=season,
    )

    try:
        service = OpenRouterService()
        response = service.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            model=prompt.model,
            json_response=True,
        )

        validator = AIResponseValidator()
        validated = validator.validate("discover_seasonal", response)

        # Create and save suggestions
        suggestions = []
        for item in validated:
            suggestion = AIDiscoverySuggestion.objects.create(
                profile=profile,
                suggestion_type="seasonal",
                search_query=item["search_query"],
                title=item["title"],
                description=item["description"],
            )
            suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} seasonal suggestions for profile {profile.id}")
        return suggestions

    except (AIUnavailableError, AIResponseError, ValidationError) as e:
        logger.warning(f"Failed to generate seasonal suggestions: {e}")
        return []


def _generate_recommended_suggestions(profile: Profile) -> List[AIDiscoverySuggestion]:
    """Generate suggestions based on user's viewing history."""
    try:
        prompt = AIPrompt.get_prompt("discover_favorites")
    except AIPrompt.DoesNotExist:
        logger.warning("discover_favorites prompt not found")
        return []

    # Get user's recently viewed recipes
    history = RecipeViewHistory.objects.filter(profile=profile).select_related("recipe").order_by("-viewed_at")[:15]
    if not history:
        return []

    # Format history list
    history_list = "\n".join(
        f"- {item.recipe.title} ({item.recipe.cuisine or item.recipe.category or 'uncategorized'})" for item in history
    )

    user_prompt = prompt.format_user_prompt(favorites=history_list)

    try:
        service = OpenRouterService()
        response = service.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            model=prompt.model,
            json_response=True,
        )

        validator = AIResponseValidator()
        validated = validator.validate("discover_favorites", response)

        # Create and save suggestions
        suggestions = []
        for item in validated:
            suggestion = AIDiscoverySuggestion.objects.create(
                profile=profile,
                suggestion_type="favorites",  # Keep type for frontend compatibility
                search_query=item["search_query"],
                title=item["title"],
                description=item["description"],
            )
            suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} recommended suggestions for profile {profile.id}")
        return suggestions

    except (AIUnavailableError, AIResponseError, ValidationError) as e:
        logger.warning(f"Failed to generate recommended suggestions: {e}")
        return []


def _generate_new_suggestions(profile: Profile) -> List[AIDiscoverySuggestion]:
    """Generate suggestions for trying something new."""
    try:
        prompt = AIPrompt.get_prompt("discover_new")
    except AIPrompt.DoesNotExist:
        logger.warning("discover_new prompt not found")
        return []

    # Get user's recent recipes from history to understand their preferences
    history = RecipeViewHistory.objects.filter(profile=profile).select_related("recipe").order_by("-viewed_at")[:15]
    if not history:
        return []

    recent_recipes = "\n".join(
        f"- {item.recipe.title} ({item.recipe.cuisine or 'unknown cuisine'}, {item.recipe.category or 'unknown category'})"
        for item in history
    )

    user_prompt = prompt.format_user_prompt(history=recent_recipes)

    try:
        service = OpenRouterService()
        response = service.complete(
            system_prompt=prompt.system_prompt,
            user_prompt=user_prompt,
            model=prompt.model,
            json_response=True,
        )

        validator = AIResponseValidator()
        validated = validator.validate("discover_new", response)

        # Create and save suggestions
        suggestions = []
        for item in validated:
            suggestion = AIDiscoverySuggestion.objects.create(
                profile=profile,
                suggestion_type="new",
                search_query=item["search_query"],
                title=item["title"],
                description=item["description"],
            )
            suggestions.append(suggestion)

        logger.info(f"Generated {len(suggestions)} try-new suggestions for profile {profile.id}")
        return suggestions

    except (AIUnavailableError, AIResponseError, ValidationError) as e:
        logger.warning(f"Failed to generate try-new suggestions: {e}")
        return []


def _get_season(dt: datetime) -> str:
    """Get the season for a given date (Northern Hemisphere)."""
    month = dt.month
    if month in (12, 1, 2):
        return "winter"
    elif month in (3, 4, 5):
        return "spring"
    elif month in (6, 7, 8):
        return "summer"
    else:
        return "autumn"
