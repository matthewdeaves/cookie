"""Tests for SSRF protection in URL validation and fetch services."""

import pytest
from unittest.mock import patch, MagicMock

from apps.core.validators import (
    validate_url,
    validate_redirect_url,
    check_response_size,
    check_content_size,
    is_blocked_ip,
    MAX_HTML_SIZE,
    MAX_IMAGE_SIZE,
    MAX_REDIRECT_HOPS,
)


# ---------------------------------------------------------------------------
# URL validation tests
# ---------------------------------------------------------------------------


class TestValidateUrl:
    """validate_url blocks internal IPs, bad schemes, and missing hostnames."""

    def test_allows_valid_http_url(self):
        with patch("apps.core.validators.resolve_hostname", return_value="93.184.216.34"):
            assert validate_url("http://example.com") == "http://example.com"

    def test_allows_valid_https_url(self):
        with patch("apps.core.validators.resolve_hostname", return_value="93.184.216.34"):
            assert validate_url("https://example.com/recipe") == "https://example.com/recipe"

    def test_blocks_file_scheme(self):
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("file:///etc/passwd")

    def test_blocks_gopher_scheme(self):
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("gopher://localhost:5432/")

    def test_blocks_javascript_scheme(self):
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("javascript:alert(1)")

    def test_blocks_data_scheme(self):
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("data:text/html,<h1>hi</h1>")

    def test_blocks_localhost(self):
        with patch("apps.core.validators.resolve_hostname", return_value="127.0.0.1"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_private_10x(self):
        with patch("apps.core.validators.resolve_hostname", return_value="10.0.0.1"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_private_172x(self):
        with patch("apps.core.validators.resolve_hostname", return_value="172.16.0.1"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_private_192x(self):
        with patch("apps.core.validators.resolve_hostname", return_value="192.168.1.1"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_link_local(self):
        with patch("apps.core.validators.resolve_hostname", return_value="169.254.169.254"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_ipv6_loopback(self):
        with patch("apps.core.validators.resolve_hostname", return_value="::1"):
            with pytest.raises(ValueError, match="blocked IP"):
                validate_url("http://example.com")

    def test_blocks_empty_hostname(self):
        with pytest.raises(ValueError, match="no hostname"):
            validate_url("http:///path")

    def test_blocks_unresolvable_hostname(self):
        with patch("apps.core.validators.resolve_hostname", side_effect=ValueError("Could not resolve")):
            with pytest.raises(ValueError, match="Could not resolve"):
                validate_url("http://nonexistent.invalid")


# ---------------------------------------------------------------------------
# IP blocking tests
# ---------------------------------------------------------------------------


class TestIsBlockedIp:
    """is_blocked_ip correctly identifies private/internal IPs."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "127.0.0.2",
            "127.255.255.255",
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.0.1",
            "192.168.255.255",
            "169.254.169.254",
            "169.254.0.1",
            "0.0.0.0",
            "0.255.255.255",
            "::1",
        ],
    )
    def test_blocked_ips(self, ip):
        assert is_blocked_ip(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "93.184.216.34",
            "8.8.8.8",
            "1.1.1.1",
            "172.32.0.1",
            "192.169.0.1",
        ],
    )
    def test_allowed_ips(self, ip):
        assert is_blocked_ip(ip) is False

    def test_invalid_ip_is_blocked(self):
        assert is_blocked_ip("not-an-ip") is True


# ---------------------------------------------------------------------------
# Redirect validation tests
# ---------------------------------------------------------------------------


class TestValidateRedirectUrl:
    """validate_redirect_url blocks redirects to internal IPs."""

    def test_blocks_redirect_to_localhost(self):
        with patch("apps.core.validators.resolve_hostname", return_value="127.0.0.1"):
            with pytest.raises(ValueError):
                validate_redirect_url("http://localhost/admin")

    def test_blocks_redirect_to_metadata(self):
        with patch("apps.core.validators.resolve_hostname", return_value="169.254.169.254"):
            with pytest.raises(ValueError):
                validate_redirect_url("http://169.254.169.254/latest/meta-data/")

    def test_allows_redirect_to_public_ip(self):
        with patch("apps.core.validators.resolve_hostname", return_value="93.184.216.34"):
            assert validate_redirect_url("https://example.com/recipe") == "https://example.com/recipe"


# ---------------------------------------------------------------------------
# Response size limit tests
# ---------------------------------------------------------------------------


class TestResponseSizeLimits:
    """check_response_size and check_content_size enforce limits."""

    def test_check_response_size_allows_small(self):
        response = MagicMock()
        response.headers = {"content-length": "1000"}
        assert check_response_size(response, MAX_HTML_SIZE) is True

    def test_check_response_size_blocks_large(self):
        response = MagicMock()
        response.headers = {"content-length": str(MAX_HTML_SIZE + 1)}
        assert check_response_size(response, MAX_HTML_SIZE) is False

    def test_check_response_size_allows_missing_header(self):
        response = MagicMock()
        response.headers = {}
        assert check_response_size(response, MAX_HTML_SIZE) is True

    def test_check_content_size_allows_small(self):
        check_content_size(b"small", MAX_HTML_SIZE)  # should not raise

    def test_check_content_size_blocks_large(self):
        with pytest.raises(ValueError, match="too large"):
            check_content_size(b"x" * (MAX_HTML_SIZE + 1), MAX_HTML_SIZE)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify security constants are set correctly."""

    def test_max_html_size(self):
        assert MAX_HTML_SIZE == 10 * 1024 * 1024

    def test_max_image_size(self):
        assert MAX_IMAGE_SIZE == 50 * 1024 * 1024

    def test_max_redirect_hops(self):
        assert MAX_REDIRECT_HOPS == 5


# ---------------------------------------------------------------------------
# PIL decompression bomb protection
# ---------------------------------------------------------------------------


class TestPilProtection:
    """PIL MAX_IMAGE_PIXELS is set to prevent decompression bombs."""

    def test_pil_max_pixels_set_in_scraper(self):
        from PIL import Image

        # Import scraper to trigger the module-level MAX_IMAGE_PIXELS setting
        import apps.recipes.services.scraper  # noqa: F401

        assert Image.MAX_IMAGE_PIXELS == 178_956_970

    def test_pil_max_pixels_set_in_image_cache(self):
        from PIL import Image
        import apps.recipes.services.image_cache  # noqa: F401

        assert Image.MAX_IMAGE_PIXELS == 178_956_970


# ---------------------------------------------------------------------------
# Image URL SSRF in scraper (FR-001)
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestImageUrlSsrf:
    """scraper._download_image must validate image URLs against SSRF blocklist."""

    @pytest.mark.asyncio
    async def test_download_image_blocks_internal_ip(self):
        """Image URL resolving to internal IP is blocked."""
        from apps.recipes.services.scraper import RecipeScraper

        scraper = RecipeScraper()
        with patch("apps.core.validators.resolve_hostname", return_value="169.254.169.254"):
            result = await scraper._download_image("http://evil.com/image.jpg")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_image_blocks_localhost(self):
        """Image URL resolving to localhost is blocked."""
        from apps.recipes.services.scraper import RecipeScraper

        scraper = RecipeScraper()
        with patch("apps.core.validators.resolve_hostname", return_value="127.0.0.1"):
            result = await scraper._download_image("http://evil.com/image.jpg")
        assert result is None

    @pytest.mark.asyncio
    async def test_download_image_blocks_file_scheme(self):
        """file:// scheme image URLs are blocked."""
        from apps.recipes.services.scraper import RecipeScraper

        scraper = RecipeScraper()
        result = await scraper._download_image("file:///etc/passwd")
        assert result is None
