"""
Regression guard for INFO-5 (R14): POST /api/recipes/scrape/ must return 400
on unexpected Content-Type (multipart/form-data), not 500.

Split from test_recipes_api.py to respect the 500-line constitutional cap
(test_recipes_api.py was at its 863-line grandfathered ceiling).
"""

import pytest


@pytest.mark.django_db(transaction=True)
class TestScrapeContentType:
    async def test_scrape_rejects_multipart_form_data(self):
        """multipart/form-data must return 400, not 500.

        Django's MultiPartParser consumes the request stream before Ninja reads
        the body. The RawPostDataException handler in cookie/urls.py converts
        this into a 400 instead of an unhandled 500.
        """
        from asgiref.sync import sync_to_async
        from apps.profiles.models import Profile
        from apps.recipes.models import SearchSource
        from django.contrib.sessions.backends.db import SessionStore
        from django.test import AsyncClient
        from django.conf import settings

        @sync_to_async
        def setup():
            p = Profile.objects.create(name="Multipart Test", avatar_color="#aabbcc")
            s = SessionStore()
            s["profile_id"] = p.id
            s.create()
            SearchSource.objects.get_or_create(
                host="allrecipes.com",
                defaults={
                    "name": "AllRecipes",
                    "search_url_template": "https://allrecipes.com/search?q={query}",
                    "is_enabled": True,
                },
            )
            return s.session_key

        session_key = await setup()

        async_client = AsyncClient()
        async_client.cookies[settings.SESSION_COOKIE_NAME] = session_key

        response = await async_client.post(
            "/api/recipes/scrape/",
            {"url": "https://allrecipes.com/recipe/123"},
            content_type="multipart/form-data",
        )

        assert response.status_code == 400
        data = response.json()
        assert "Cannot parse request body" in data["detail"]
