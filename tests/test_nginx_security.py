"""
Tests for nginx production configuration security rules.

Verifies that nginx.prod.conf contains proper blocking rules for:
- Dotfiles (except .well-known)
- Sensitive file extensions (scanner-bait)
- Scanner-targeted filenames
- Security headers
- SPA catch-all behavior
"""

import re
from pathlib import Path

import pytest

NGINX_PROD_CONF = Path(__file__).parent.parent / "nginx" / "nginx.prod.conf"
SECURITY_HEADERS_CONF = Path(__file__).parent.parent / "nginx" / "security-headers.conf"


@pytest.fixture
def nginx_config():
    """Read the production nginx config."""
    return NGINX_PROD_CONF.read_text()


@pytest.fixture
def security_headers():
    """Read the security headers config."""
    return SECURITY_HEADERS_CONF.read_text()


class TestNginxDotfileBlocking:
    """Dotfiles must return 404 (except .well-known)."""

    def test_dotfile_block_rule_exists(self, nginx_config):
        assert re.search(r"location\s+~\s+/\\\..*well-known", nginx_config), (
            "Missing dotfile blocking rule (location ~ /\\.(?!well-known))"
        )

    def test_dotfile_returns_404(self, nginx_config):
        # The block should use return 404
        block = re.search(r"location\s+~\s+/\\\..*?\{(.*?)\}", nginx_config, re.DOTALL)
        assert block, "Dotfile location block not found"
        assert "return 404" in block.group(1)


class TestNginxSourcemapBlocking:
    """Sourcemap files must return 404."""

    def test_sourcemap_block_rule_exists(self, nginx_config):
        assert re.search(r"location\s+~\*\s+\\\.map\$", nginx_config), (
            "Missing sourcemap blocking rule (location ~* \\.map$)"
        )

    def test_sourcemap_block_returns_404(self, nginx_config):
        block = re.search(r"location\s+~\*\s+\\\.map\$\s*\{(.*?)\}", nginx_config, re.DOTALL)
        assert block, "Sourcemap blocking location block not found"
        assert "return 404" in block.group(1)


class TestNginxSensitiveExtensions:
    """Sensitive file extensions must return 404."""

    # Extensions that scanners commonly probe
    REQUIRED_EXTENSIONS = [
        "sql",
        "sqlite3",
        "bak",
        "log",
        "conf",
        "cfg",
        "ini",
        "py",
        "yaml",
        "yml",
        "sh",
        "php",
    ]

    def test_extension_block_rule_exists(self, nginx_config):
        assert re.search(r"location\s+~\*\s+\\\..*\$", nginx_config), "Missing sensitive extension blocking rule"

    @pytest.mark.parametrize("ext", REQUIRED_EXTENSIONS)
    def test_extension_blocked(self, nginx_config, ext):
        # Find the extension blocking location block
        block = re.search(r"location\s+~\*\s+\\\.\(([^)]+)\)\$", nginx_config)
        assert block, "Extension blocking location not found"
        extensions = block.group(1).split("|")
        assert ext in extensions, f"Extension .{ext} not blocked in nginx config. Blocked: {extensions}"

    def test_extension_block_returns_404(self, nginx_config):
        block = re.search(
            r"location\s+~\*\s+\\\.\([^)]+\)\$\s*\{(.*?)\}",
            nginx_config,
            re.DOTALL,
        )
        assert block, "Extension blocking location block not found"
        assert "return 404" in block.group(1)


class TestNginxScannerFilenames:
    """Common scanner-targeted filenames must return 404."""

    # Plain filenames (not regex) — test checks they appear in the nginx block
    REQUIRED_FILENAMES = [
        "Dockerfile",
        "Makefile",
        "Thumbs",
        "requirements",
        "Pipfile",
        "manage",
        "server-status",
        "server-info",
    ]

    def test_filename_block_rule_exists(self, nginx_config):
        assert re.search(r"location\s+~\*\s+\^/\(.*Dockerfile", nginx_config), "Missing scanner filename blocking rule"

    @pytest.mark.parametrize("filename", REQUIRED_FILENAMES)
    def test_filename_blocked(self, nginx_config, filename):
        block = re.search(r"location\s+~\*\s+\^/\(([^)]+)\)\$", nginx_config)
        assert block, "Filename blocking location not found"
        assert filename in block.group(1), (
            f"Filename {filename} not blocked in nginx config. Block contains: {block.group(1)}"
        )


class TestNginxSecurityHeaders:
    """Security headers must be present in the shared include."""

    REQUIRED_HEADERS = [
        ("Strict-Transport-Security", r"max-age=\d+.*preload"),
        ("X-Content-Type-Options", "nosniff"),
        ("X-Frame-Options", "SAMEORIGIN"),
        ("Content-Security-Policy", "default-src"),
        ("Referrer-Policy", "strict-origin"),
        ("Permissions-Policy", "camera="),
        ("Cross-Origin-Opener-Policy", "same-origin"),
        ("Cross-Origin-Resource-Policy", "same-origin"),
        ("Cross-Origin-Embedder-Policy", "credentialless"),
        ("X-XSS-Protection", "0"),
        ("X-Permitted-Cross-Domain-Policies", "none"),
    ]

    @pytest.mark.parametrize("header,value_pattern", REQUIRED_HEADERS)
    def test_header_present(self, security_headers, header, value_pattern):
        # Headers set via add_header directive
        pattern = rf"add_header\s+{re.escape(header)}\s+.*{value_pattern}"
        assert re.search(pattern, security_headers, re.IGNORECASE), (
            f"Missing security header: {header} with pattern {value_pattern}"
        )

    def test_server_tokens_off(self, nginx_config):
        assert "server_tokens off" in nginx_config, "server_tokens must be set to off to hide nginx version"


class TestNginxCSP:
    """Content Security Policy must be strict."""

    @staticmethod
    def _extract_csp(security_headers):
        """Extract the full CSP value from the security headers config."""
        match = re.search(r'Content-Security-Policy\s+"([^"]+)"', security_headers)
        assert match, "CSP header not found in security-headers.conf"
        return match.group(1)

    def test_no_unsafe_inline_in_script_src(self, security_headers):
        csp = self._extract_csp(security_headers)
        script_src = re.search(r"script-src\s+([^;]+)", csp)
        if script_src:
            assert "'unsafe-inline'" not in script_src.group(1), "CSP script-src must not contain 'unsafe-inline'"

    def test_no_unsafe_eval_in_script_src(self, security_headers):
        csp = self._extract_csp(security_headers)
        script_src = re.search(r"script-src\s+([^;]+)", csp)
        if script_src:
            assert "'unsafe-eval'" not in script_src.group(1), "CSP script-src must not contain 'unsafe-eval'"

    def test_frame_ancestors_present(self, security_headers):
        csp = self._extract_csp(security_headers)
        assert "frame-ancestors" in csp, "CSP must include frame-ancestors directive"


class TestNginxRouting:
    """Verify correct routing configuration."""

    def test_api_proxied_to_django(self, nginx_config):
        assert re.search(
            r"location\s+/api/.*proxy_pass\s+http://django",
            nginx_config,
            re.DOTALL,
        )

    def test_api_no_cache(self, nginx_config):
        # API responses should have Cache-Control: no-store
        api_block = re.search(r"location\s+/api/\s*\{(.*?)\}", nginx_config, re.DOTALL)
        assert api_block, "/api/ location block not found"
        assert "no-store" in api_block.group(1), "API responses must have Cache-Control: no-store"

    def test_static_has_long_cache(self, nginx_config):
        static_block = re.search(r"location\s+/static/\s*\{(.*?)\}", nginx_config, re.DOTALL)
        assert static_block
        assert "expires 1y" in static_block.group(1) or "immutable" in static_block.group(1)

    def test_spa_catchall_exists(self, nginx_config):
        assert "try_files $uri $uri/ /index.html" in nginx_config

    def test_gunicorn_localhost_only(self, nginx_config):
        assert "127.0.0.1:8000" in nginx_config, "Gunicorn must bind to localhost only"

    def test_client_max_body_size(self, nginx_config):
        assert re.search(r"client_max_body_size\s+\d+m", nginx_config), "client_max_body_size must be set"


ENTRYPOINT_PROD = Path(__file__).parent.parent / "entrypoint.prod.sh"


class TestEntrypointSecurity:
    """Security checks for production entrypoint script."""

    @pytest.fixture
    def entrypoint(self):
        return ENTRYPOINT_PROD.read_text()

    def test_cron_file_permissions_restrictive(self, entrypoint):
        """Cron env file contains secrets — must not be world-readable."""
        assert "chmod 0600 /etc/cron.d/cookie-cleanup" in entrypoint, (
            "Cron file must use chmod 0600, not 0644 — it contains DATABASE_URL and SECRET_KEY"
        )
        assert "chmod 0644 /etc/cron.d/cookie-cleanup" not in entrypoint, (
            "Cron file must not use world-readable 0644 permissions"
        )

    def test_secret_key_file_permissions(self, entrypoint):
        """Generated secret key file must be owner-only."""
        assert "chmod 600" in entrypoint, "SECRET_KEY file must have restrictive permissions"
