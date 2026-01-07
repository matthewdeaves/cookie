"""URL configuration for cookie project."""

from django.urls import path, include
from ninja import NinjaAPI

from apps.core.api import router as settings_router
from apps.profiles.api import router as profiles_router
from apps.recipes.api import router as recipes_router
from apps.recipes.api_user import (
    collections_router,
    favorites_router,
    history_router,
)

api = NinjaAPI()
api.add_router('/settings', settings_router)
api.add_router('/profiles', profiles_router)
api.add_router('/recipes', recipes_router)
api.add_router('/favorites', favorites_router)
api.add_router('/collections', collections_router)
api.add_router('/history', history_router)


@api.get('/health')
def health(request):
    return {'status': 'ok'}


urlpatterns = [
    path('api/', api.urls),
    path('legacy/', include('apps.legacy.urls')),
]
