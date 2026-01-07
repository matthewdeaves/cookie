"""
Core API endpoints.
"""

from ninja import Router, Schema

from .models import AppSettings

router = Router(tags=['settings'])


class SettingsOut(Schema):
    ai_available: bool


@router.get('/', response=SettingsOut)
def get_settings(request):
    """
    Get application settings.

    Returns whether AI features are available (API key configured).
    """
    settings = AppSettings.get()
    return {
        'ai_available': bool(settings.openrouter_api_key),
    }
