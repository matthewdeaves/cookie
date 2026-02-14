"""URL configuration for cookie project."""

from typing import Any, Optional

from django.http import HttpRequest
from django.urls import path, include
from ninja import NinjaAPI
from ninja.security import APIKeyCookie

from apps.ai.api import router as ai_router
from apps.core.api import router as system_router
from apps.profiles.api import router as profiles_router
from apps.recipes.api import router as recipes_router
from apps.recipes.api_user import (
    collections_router,
    favorites_router,
    history_router,
)
from apps.recipes.sources_api import router as sources_router


class CsrfCheck(APIKeyCookie):
    """CSRF check that allows unauthenticated requests.

    This auth class enables CSRF checking (via APIKeyCookie) but doesn't
    require the user to be authenticated. It always returns True for the
    authentication check, but the CSRF token must be valid.
    """

    param_name: str = "csrftoken"

    def authenticate(self, request: HttpRequest, key: Optional[str]) -> Optional[Any]:
        # Always allow - we just want CSRF checking, not auth
        return True


api = NinjaAPI(auth=CsrfCheck())
api.add_router("/ai", ai_router)
api.add_router("/profiles", profiles_router)
api.add_router("/recipes", recipes_router)
api.add_router("/favorites", favorites_router)
api.add_router("/collections", collections_router)
api.add_router("/history", history_router)
api.add_router("/sources", sources_router)
api.add_router("/system", system_router)


@api.get("/health")
def health(request):
    return {"status": "ok"}


urlpatterns = [
    path("api/", api.urls),
    path("legacy/", include("apps.legacy.urls")),
]
