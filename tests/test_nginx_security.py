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
        ("X-Frame-Options", "DENY"),
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

    def test_absolute_redirect_off(self, nginx_config):
        """Trailing-slash redirects must not build absolute `http://` URLs
        behind a TLS-terminating proxy (pentest round 3). `absolute_redirect
        off` makes nginx emit relative Location headers so the browser reuses
        the original request scheme (https)."""
        assert re.search(r"^\s*absolute_redirect\s+off\s*;", nginx_config, re.MULTILINE), (
            "nginx.prod.conf must set `absolute_redirect off;` so /admin → /admin/ "
            "redirects do not leak `Location: http://…` behind an HTTPS proxy."
        )


class TestNginxWebManifestMimeType:
    """Pentest round 4 / L1: /site.webmanifest must be served with
    application/manifest+json, not the http-level application/octet-stream
    default. Under `X-Content-Type-Options: nosniff`, Chromium and Firefox
    refuse to treat an octet-stream response as a PWA manifest, breaking
    "Add to Home Screen"."""

    def test_webmanifest_location_block_exists(self, nginx_config):
        assert re.search(r"location\s+=\s+/site\.webmanifest\s*\{", nginx_config), (
            "nginx.prod.conf must define `location = /site.webmanifest` so "
            "the PWA manifest can set its own Content-Type."
        )

    def test_webmanifest_default_type_is_manifest_json(self, nginx_config):
        block = re.search(
            r"location\s+=\s+/site\.webmanifest\s*\{(.*?)\}",
            nginx_config,
            re.DOTALL,
        )
        assert block, "webmanifest location block not found"
        body = block.group(1)
        assert re.search(r"default_type\s+application/manifest\+json\s*;", body), (
            "location = /site.webmanifest must set "
            "`default_type application/manifest+json;` so browsers accept "
            "the file as a PWA manifest under nosniff."
        )


class TestNginxErrorPagesDoNotLeakNginx:
    """Pentest round 4 / L2: nginx's stock `<center>nginx</center>` error
    body must not be served on 403 (directory-listing attempts on /assets/,
    /media/) or 404 responses. Route both through an internal named handler
    that emits an empty body instead."""

    def test_error_page_403_rewritten_to_404(self, nginx_config):
        assert re.search(
            r"error_page\s+403\s+=404\s+@\w+\s*;",
            nginx_config,
        ), (
            "nginx.prod.conf must rewrite 403 to 404 via a named location "
            "so directory-listing 403s stop leaking the stock nginx error page."
        )

    def test_error_page_404_routed_to_named_handler(self, nginx_config):
        assert re.search(r"error_page\s+404\s+@\w+\s*;", nginx_config), (
            "nginx.prod.conf must route 404 to a named internal handler "
            "so nginx-generated 404s stop leaking the stock nginx error page."
        )

    def test_named_error_handler_is_internal(self, nginx_config):
        block = re.search(
            r"location\s+@not_found\s*\{(.*?)\n\s*\}",
            nginx_config,
            re.DOTALL,
        )
        assert block, "Named `@not_found` error handler not found"
        body = block.group(1)
        assert re.search(r"^\s*internal\s*;", body, re.MULTILINE), (
            "`@not_found` must be marked `internal;` so clients cannot hit it directly."
        )
        assert re.search(r'return\s+404\s+""\s*;', body), (
            '`@not_found` must `return 404 "";` — empty body so the nginx signature cannot appear in the response body.'
        )
        assert "security-headers.conf" in body, "`@not_found` must include the standard security headers."


ENTRYPOINT_PROD = Path(__file__).parent.parent / "entrypoint.prod.sh"


class TestEntrypointSecurity:
    """Security checks for production entrypoint script."""

    @pytest.fixture
    def entrypoint(self):
        return ENTRYPOINT_PROD.read_text()

    def test_no_secrets_in_cron_config(self, entrypoint):
        """Entrypoint must not write SECRET_KEY or DATABASE_URL to cron files.

        After 015-security-review-fixes, supercronic inherits env from the
        entrypoint process. No secrets are written to disk.
        """
        assert "/etc/cron.d/cookie-cleanup" not in entrypoint, (
            "Entrypoint must not write /etc/cron.d/cookie-cleanup — use supercronic with inherited env"
        )
        assert "supercronic" in entrypoint, "Entrypoint must launch supercronic as the scheduler"

    def test_secret_key_file_permissions(self, entrypoint):
        """Generated secret key file must be owner-only."""
        assert "chmod 600" in entrypoint, "SECRET_KEY file must have restrictive permissions"
