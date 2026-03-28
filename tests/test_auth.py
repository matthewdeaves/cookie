"""Tests for authentication (home and passkey modes only)."""

import pytest


@pytest.mark.django_db
class TestPrivacyPolicy:
    def test_accessible_without_auth(self, client):
        response = client.get("/privacy/")
        assert response.status_code == 200

    def test_contains_required_elements(self, client):
        response = client.get("/privacy/")
        content = response.content.decode()
        assert "what data we collect" in content.lower()
        assert "ICO" in content or "Information Commissioner" in content
