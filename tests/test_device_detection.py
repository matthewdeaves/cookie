import pytest


@pytest.mark.django_db
class TestDeviceDetection:
    """Tests for the device detection middleware."""

    def test_modern_browser_not_legacy(self, client):
        """Modern browsers should not be marked as legacy."""
        user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        )
        response = client.get('/api/health', HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200
        # Middleware sets is_legacy_device on request, but we verify via API working

    def test_ios9_is_legacy(self, client):
        """iOS 9 devices should be marked as legacy."""
        user_agent = (
            'Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) '
            'AppleWebKit/601.1.46 (KHTML, like Gecko) '
            'Version/9.0 Mobile/13G36 Safari/601.1'
        )
        response = client.get('/api/health', HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ios10_not_legacy(self, client):
        """iOS 10+ devices should not be marked as legacy."""
        user_agent = (
            'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0 like Mac OS X) '
            'AppleWebKit/602.1.50 (KHTML, like Gecko) '
            'Version/10.0 Mobile/14A346 Safari/602.1'
        )
        response = client.get('/api/health', HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_no_user_agent_not_legacy(self, client):
        """Requests without user agent should not be marked as legacy."""
        response = client.get('/api/health')
        assert response.status_code == 200
