"""URL configuration for cookie project."""

from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI()


@api.get('/health')
def health(request):
    return {'status': 'ok'}


urlpatterns = [
    path('api/', api.urls),
]
