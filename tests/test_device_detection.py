import pytest
from django.test import RequestFactory

from apps.core.middleware import DeviceDetectionMiddleware


class TestDeviceDetection:
    """Tests for the device detection middleware.

    Note: Actual redirects are handled by Nginx (see nginx/nginx.conf).
    These tests verify the middleware correctly sets request.is_legacy_device.
    """

    def _check(self, user_agent=None):
        """Run middleware and return request.is_legacy_device."""
        rf = RequestFactory()
        kwargs = {}
        if user_agent is not None:
            kwargs["HTTP_USER_AGENT"] = user_agent
        request = rf.get("/", **kwargs)
        middleware = DeviceDetectionMiddleware(lambda r: r)
        middleware(request)
        return request.is_legacy_device

    # === Modern browsers (should NOT be legacy) ===

    def test_modern_chrome_not_legacy(self):
        """Modern Chrome should not be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
            is False
        )

    def test_modern_firefox_not_legacy(self):
        """Modern Firefox should not be marked as legacy."""
        assert self._check("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0") is False

    def test_chromium_edge_not_legacy(self):
        """Chromium-based Edge should not be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            )
            is False
        )

    def test_ios11_not_legacy(self):
        """iOS 11+ devices should not be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) "
                "AppleWebKit/604.1.38 (KHTML, like Gecko) "
                "Version/11.0 Mobile/15A372 Safari/604.1"
            )
            is False
        )

    def test_ios17_not_legacy(self):
        """Latest iOS should not be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) "
                "Version/17.0 Mobile/15E148 Safari/604.1"
            )
            is False
        )

    def test_chrome_60_not_legacy(self):
        """Chrome 60+ should not be marked as legacy (ES6 module support)."""
        assert (
            self._check(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/60.0.3112.113 Safari/537.36"
            )
            is False
        )

    def test_firefox_55_not_legacy(self):
        """Firefox 55+ should not be marked as legacy (ES6 module support)."""
        assert self._check("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:55.0) Gecko/20100101 Firefox/55.0") is False

    def test_no_user_agent_not_legacy(self):
        """Requests without user agent should not be marked as legacy."""
        assert self._check() is False

    # === Legacy browsers (SHOULD be legacy) ===

    def test_ios9_is_legacy(self):
        """iOS 9 devices should be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (iPad; CPU OS 9_3_5 like Mac OS X) "
                "AppleWebKit/601.1.46 (KHTML, like Gecko) "
                "Version/9.0 Mobile/13G36 Safari/601.1"
            )
            is True
        )

    def test_ios10_is_legacy(self):
        """iOS 10 devices should be marked as legacy (< 11)."""
        assert (
            self._check(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_3 like Mac OS X) "
                "AppleWebKit/603.3.8 (KHTML, like Gecko) "
                "Version/10.0 Mobile/14G60 Safari/602.1"
            )
            is True
        )

    def test_ie11_is_legacy(self):
        """Internet Explorer 11 should be marked as legacy."""
        assert self._check("Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko") is True

    def test_ie10_is_legacy(self):
        """Internet Explorer 10 should be marked as legacy."""
        assert self._check("Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)") is True

    def test_edge_legacy_is_legacy(self):
        """Edge Legacy (non-Chromium) should be marked as legacy."""
        assert (
            self._check(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/64.0.3282.140 Safari/537.36 Edge/18.17763"
            )
            is True
        )

    def test_chrome_59_is_legacy(self):
        """Chrome 59 should be marked as legacy (< 60)."""
        assert (
            self._check(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/59.0.3071.115 Safari/537.36"
            )
            is True
        )

    def test_firefox_54_is_legacy(self):
        """Firefox 54 should be marked as legacy (< 55)."""
        assert self._check("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0") is True
