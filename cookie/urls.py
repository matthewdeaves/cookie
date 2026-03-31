"""URL configuration for cookie project."""

from django.conf import settings
from django.urls import path, include
from ninja import NinjaAPI

from apps.ai.api import router as ai_router
from apps.ai.api_remix import router as ai_remix_router
from apps.ai.api_scaling import router as ai_scaling_router
from apps.ai.api_discover import router as ai_discover_router
from apps.ai.api_quotas import router as ai_quota_router
from apps.core.api import router as system_router
from apps.profiles.api import router as profiles_router
from apps.recipes.api import router as recipes_router
from apps.recipes.api_user import (
    collections_router,
    favorites_router,
    history_router,
)
from apps.recipes.sources_api import router as sources_router

api = NinjaAPI()
api.add_router("/ai", ai_router)
api.add_router("/ai", ai_remix_router)
api.add_router("/ai", ai_scaling_router)
api.add_router("/ai", ai_discover_router)
api.add_router("/ai", ai_quota_router)
api.add_router("/profiles", profiles_router)
api.add_router("/recipes", recipes_router)
api.add_router("/favorites", favorites_router)
api.add_router("/collections", collections_router)
api.add_router("/history", history_router)
api.add_router("/sources", sources_router)
api.add_router("/system", system_router)

# Auth router is always mounted but endpoints check AUTH_MODE internally
from apps.core.auth_api import router as auth_router

api.add_router("/auth", auth_router)

# Passkey and device code routers — endpoints check AUTH_MODE internally
from apps.core.passkey_api import router as passkey_router
from apps.core.device_code_api import router as device_code_router

api.add_router("/auth/passkey", passkey_router)
api.add_router("/auth/device", device_code_router)


from apps.core.views import PrivacyPolicyView

urlpatterns = [
    path("api/", api.urls),
    path("privacy/", PrivacyPolicyView.as_view(), name="privacy-policy"),
    path("legacy/", include("apps.legacy.urls")),
]
