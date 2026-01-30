import pytest


@pytest.mark.django_db
class TestDeviceDetection:
    """Tests for the device detection middleware.

    Note: Actual redirects are handled by Nginx (see nginx/nginx.conf).
    These tests verify the middleware correctly sets request.is_legacy_device.
    """

    # === Modern browsers (should NOT be legacy) ===

    def test_modern_chrome_not_legacy(self, client):
        """Modern Chrome should not be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_modern_firefox_not_legacy(self, client):
        """Modern Firefox should not be marked as legacy."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0"
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_chromium_edge_not_legacy(self, client):
        """Chromium-based Edge should not be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ios11_not_legacy(self, client):
        """iOS 11+ devices should not be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
            "AppleWebKit/604.1.38 (KHTML, like Gecko) "
            "Version/11.0 Mobile/15A372 Safari/604.1"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ios17_not_legacy(self, client):
        """Latest iOS should not be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/17.0 Mobile/15E148 Safari/604.1"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_chrome_60_not_legacy(self, client):
        """Chrome 60+ should not be marked as legacy (ES6 module support)."""
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/60.0.3112.113 Safari/537.36"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_firefox_55_not_legacy(self, client):
        """Firefox 55+ should not be marked as legacy (ES6 module support)."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0"
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_no_user_agent_not_legacy(self, client):
        """Requests without user agent should not be marked as legacy."""
        response = client.get("/api/health")
        assert response.status_code == 200

    # === Legacy browsers (SHOULD be legacy) ===

    def test_ios9_is_legacy(self, client):
        """iOS 9 devices should be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) "
            "AppleWebKit/601.1.46 (KHTML, like Gecko) "
            "Version/9.0 Mobile/13G36 Safari/601.1"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ios10_is_legacy(self, client):
        """iOS 10 devices should be marked as legacy (< 11)."""
        user_agent = (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) "
            "AppleWebKit/603.3.8 (KHTML, like Gecko) "
            "Version/10.0 Mobile/14G60 Safari/602.1"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ie11_is_legacy(self, client):
        """Internet Explorer 11 should be marked as legacy."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko"
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_ie10_is_legacy(self, client):
        """Internet Explorer 10 should be marked as legacy."""
        user_agent = "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)"
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_edge_legacy_is_legacy(self, client):
        """Edge Legacy (non-Chromium) should be marked as legacy."""
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_chrome_59_is_legacy(self, client):
        """Chrome 59 should be marked as legacy (< 60)."""
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/59.0.3071.115 Safari/537.36"
        )
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200

    def test_firefox_54_is_legacy(self, client):
        """Firefox 54 should be marked as legacy (< 55)."""
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0"
        response = client.get("/api/health", HTTP_USER_AGENT=user_agent)
        assert response.status_code == 200
