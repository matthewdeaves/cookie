"""The legacy profile picker must hand out a CSRF cookie before any API call is made."""

import pytest
from django.test import Client


@pytest.mark.django_db
class TestLegacyPickerCsrfCookie:
    def test_profile_selector_sets_csrf_cookie(self):
        response = Client().get("/legacy/")

        assert response.status_code == 200
        assert "csrftoken" in response.cookies

    def test_select_profile_succeeds_with_the_cookie_from_the_picker(self):
        from apps.profiles.models import Profile

        profile = Profile.objects.create(name="First Visit", avatar_color="#112233")
        client = Client(enforce_csrf_checks=True)

        picker = client.get("/legacy/")
        token = picker.cookies["csrftoken"].value
        response = client.post(
            f"/api/profiles/{profile.id}/select/",
            content_type="application/json",
            HTTP_X_CSRFTOKEN=token,
        )

        assert response.status_code == 200
