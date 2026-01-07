"""URL configuration for cookie project."""

from django.urls import path
from ninja import NinjaAPI

from apps.profiles.api import router as profiles_router
from apps.recipes.api import router as recipes_router

api = NinjaAPI()
api.add_router('/profiles', profiles_router)
api.add_router('/recipes', recipes_router)


@api.get('/health')
def health(request):
    return {'status': 'ok'}


urlpatterns = [
    path('api/', api.urls),
]
