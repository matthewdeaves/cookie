"""
Tests for SSRF protection in URL validation (T004).

Verifies that the URL validator blocks internal IPs, private networks,
dangerous schemes, and DNS rebinding attacks.
"""

import socket
from unittest.mock import patch

import pytest

from apps.core.validators import is_blocked_ip, resolve_hostname, validate_url


class TestIsBlockedIp:
    """Tests for is_blocked_ip function."""

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "127.0.0.2",
            "10.0.0.1",
            "10.255.255.255",
            "172.16.0.1",
            "172.31.255.255",
            "192.168.1.1",
            "192.168.0.1",
            "169.254.169.254",  # AWS metadata endpoint
            "169.254.0.1",
            "0.0.0.0",
            "0.0.0.1",
        ],
    )
    def test_blocked_private_ips(self, ip):
        """Private and reserved IPs must be blocked."""
        assert is_blocked_ip(ip) is True

    @pytest.mark.parametrize(
        "ip",
        [
            "8.8.8.8",
            "1.1.1.1",
            "93.184.216.34",  # example.com
            "104.21.0.1",
        ],
    )
    def test_allowed_public_ips(self, ip):
        """Public IPs must be allowed."""
        assert is_blocked_ip(ip) is False

    def test_invalid_ip_is_blocked(self):
        """Invalid IP strings are treated as blocked."""
        assert is_blocked_ip("not-an-ip") is True
        assert is_blocked_ip("") is True

    @pytest.mark.parametrize(
        "ip",
        [
            "::1",  # IPv6 loopback
            "fc00::1",  # IPv6 unique local
            "fe80::1",  # IPv6 link-local
        ],
    )
    def test_blocked_ipv6_addresses(self, ip):
        """IPv6 private/reserved addresses must be blocked."""
        assert is_blocked_ip(ip) is True


class TestResolveHostname:
    """Tests for resolve_hostname function."""

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_resolves_valid_hostname(self, mock_getaddrinfo):
        """Valid hostname returns resolved IP."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        result = resolve_hostname("example.com")
        assert result == "93.184.216.34"

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_unresolvable_hostname_raises(self, mock_getaddrinfo):
        """Unresolvable hostname raises ValueError."""
        mock_getaddrinfo.side_effect = socket.gaierror("Name resolution failed")
        with pytest.raises(ValueError, match="Could not resolve hostname"):
            resolve_hostname("definitely-not-a-real-host.invalid")

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_empty_results_raises(self, mock_getaddrinfo):
        """Empty DNS results raise ValueError."""
        mock_getaddrinfo.return_value = []
        with pytest.raises(ValueError, match="Could not resolve hostname"):
            resolve_hostname("empty-results.example.com")


class TestValidateUrl:
    """Tests for validate_url function."""

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_allows_valid_external_url(self, mock_getaddrinfo):
        """Valid external HTTPS URL passes validation with pinned DNS."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        result = validate_url("https://example.com/recipe")
        assert result.url == "https://example.com/recipe"
        assert result.hostname == "example.com"
        assert result.ip == "93.184.216.34"
        assert "example.com:443:93.184.216.34" in result.curl_resolve

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_allows_http_url(self, mock_getaddrinfo):
        """Valid external HTTP URL passes validation with pinned DNS."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 0))]
        result = validate_url("http://example.com/recipe")
        assert result.url == "http://example.com/recipe"
        assert result.ip == "93.184.216.34"

    def test_blocks_file_scheme(self):
        """file:// URLs must be rejected."""
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("file:///etc/passwd")

    def test_blocks_ftp_scheme(self):
        """ftp:// URLs must be rejected."""
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("ftp://evil.com/data")

    def test_blocks_javascript_scheme(self):
        """javascript: URLs must be rejected."""
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("javascript:alert(1)")

    def test_blocks_data_scheme(self):
        """data: URLs must be rejected."""
        with pytest.raises(ValueError, match="scheme not allowed"):
            validate_url("data:text/html,<h1>hello</h1>")

    def test_blocks_empty_hostname(self):
        """URLs with no hostname must be rejected."""
        with pytest.raises(ValueError, match="no hostname"):
            validate_url("http://")

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_blocks_localhost_resolution(self, mock_getaddrinfo):
        """URLs resolving to 127.0.0.1 must be blocked."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0))]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_url("https://evil.com/redirect-to-localhost")

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_blocks_internal_ip_resolution(self, mock_getaddrinfo):
        """URLs resolving to private IPs must be blocked (DNS rebinding)."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0))]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_url("https://attacker.com/rebind")

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_blocks_metadata_ip_resolution(self, mock_getaddrinfo):
        """URLs resolving to cloud metadata IPs must be blocked."""
        mock_getaddrinfo.return_value = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("169.254.169.254", 0))]
        with pytest.raises(ValueError, match="blocked IP"):
            validate_url("https://attacker.com/metadata")

    @patch("apps.core.validators.socket.getaddrinfo")
    def test_blocks_unresolvable_hostname(self, mock_getaddrinfo):
        """URLs with unresolvable hostnames must be rejected."""
        mock_getaddrinfo.side_effect = socket.gaierror("Name resolution failed")
        with pytest.raises(ValueError, match="Could not resolve hostname"):
            validate_url("https://definitely-not-real.invalid/page")
