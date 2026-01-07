"""URL configuration for cookie project."""

from django.urls import path
from ninja import NinjaAPI

from apps.profiles.api import router as profiles_router

api = NinjaAPI()
api.add_router('/profiles', profiles_router)


@api.get('/health')
def health(request):
    return {'status': 'ok'}


urlpatterns = [
    path('api/', api.urls),
]
