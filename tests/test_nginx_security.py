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

    def test_style_src_unsafe_inline_allowed(self, security_headers):
        # 'unsafe-inline' is intentionally allowed for style-src to support
        # Sonner's dynamic <style> injection (toast notifications) and other
        # third-party libraries. CSS injection is far lower risk than JS injection
        # since CSS cannot execute code. script-src remains strict (no unsafe-inline).
        csp = self._extract_csp(security_headers)
        style_src = re.search(r"style-src\s+([^;]+)", csp)
        if style_src:
            assert "'unsafe-inline'" in style_src.group(1), (
                "style-src must allow 'unsafe-inline' for Sonner toast CSS injection"
            )

    def test_no_unsafe_inline_in_script_src_from_style_change(self, security_headers):
        # Verify that adding unsafe-inline to style-src did not accidentally
        # add it to script-src as well.
        csp = self._extract_csp(security_headers)
        script_src = re.search(r"script-src\s+([^;]+)", csp)
        if script_src:
            assert "'unsafe-inline'" not in script_src.group(1), (
                "script-src must never contain 'unsafe-inline'"
            )


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
            "nginx.prod.conf must set `absolute_redirect off;` so any "
            "nginx-emitted trailing-slash redirect (e.g. a future prefix "
            "location that introduces one) does not leak `Location: http://…` "
            "behind an HTTPS proxy."
        )

    def test_admin_is_not_proxied_to_django(self, nginx_config):
        """Pentest round 6 / F-13: the legacy `location /admin/ { proxy_pass
        http://django; }` block caused nginx to emit a 301 trailing-slash
        redirect on `/admin` (no slash) with a default body that contained
        `<center>nginx</center>`. Django's admin isn't URL-mounted anyway, so
        the block was dead code. Removing it lets /admin fall through to the
        scanner-prefix 404 handler."""
        assert not re.search(
            r"location\s+/admin/\s*\{[^}]*proxy_pass\s+http://django",
            nginx_config,
            re.DOTALL,
        ), (
            "nginx.prod.conf must NOT proxy /admin/ to Django. Django's admin "
            "is not URL-mounted (see cookie/urls.py). The old proxy block "
            "caused the F-13 nginx-bodied 301 leak on /admin and should stay "
            "removed."
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
        # `return 404 "";` is a nginx no-op (zero-length body falls back to
        # the default error page, leaking `<center>nginx</center>`). The body
        # must be non-empty. Asserting the exact `Not Found\n` string here so
        # no future edit silently reverts to the broken pattern.
        assert re.search(r'return\s+404\s+"Not Found\\n"\s*;', body), (
            '`@not_found` must `return 404 "Not Found\\n";` — a non-empty body '
            "so nginx does not fall back to its default error page. Empty-string "
            "bodies are silently dropped and re-expose the stock "
            "`<center>nginx</center>` footer."
        )
        assert "security-headers.conf" in body, "`@not_found` must include the standard security headers."


class TestNginxScannerBlocksReturnNonEmptyBody:
    """Pentest round 6 / F-1: scanner-blocking locations must return an
    EXPLICIT non-empty body (`return 404 "Not Found\\n";`) and include the
    security headers directly.

    Rationale: pentest round 5 (v1.47.0) attempted to ship `return 404 "";`
    on every scanner block. That pattern is a nginx no-op — a zero-length
    body is silently dropped and the HTTP core falls back to the default
    error page, which re-exposes the stock `<center>nginx</center>` footer.
    The fix is an explicit non-empty body; this test locks that in so no
    future edit can silently revert to the broken pattern.

    The @not_found named handler (covered by TestNginxErrorPagesDoNotLeakNginx)
    remains the primary defence for nginx-generated 4xx (e.g. autoindex 403
    on /assets/, /media/); this test covers the explicit `return 404;` blocks.
    """

    # Match each block by a distinctive snippet that appears only in its
    # location pattern, then grab the body between the outermost braces.
    # (Using a permissive block-body regex so nested parens in the regex
    # location patterns do not break the match.)
    BLOCK_SIGNATURES = [
        ("dotfile", r"location\s+~\s+/\\\.\(\?!well-known\)[^{]*\{([^}]*)\}"),
        ("sourcemap", r"location\s+~\*\s+\\\.map\$[^{]*\{([^}]*)\}"),
        ("sensitive-extensions", r"location\s+~\*\s+\\\.\(sql\|[^{]*\{([^}]*)\}"),
        ("scanner-filenames", r"location\s+~\*\s+\^/\(Dockerfile\|[^{]*\{([^}]*)\}"),
    ]

    @pytest.mark.parametrize("label,block_regex", BLOCK_SIGNATURES)
    def test_block_returns_non_empty_body(self, nginx_config, label, block_regex):
        block_match = re.search(block_regex, nginx_config, re.DOTALL)
        assert block_match, f"Scanner-block location not found: {label}"
        body = block_match.group(1)
        # Guard against regressing to the v1.46 / v1.47 bug.
        assert not re.search(r'return\s+404\s+""\s*;', body), (
            f"Scanner-block {label!r} uses `return 404 \"\";` which is a "
            f"nginx no-op — the zero-length body is dropped and the default "
            f"`<center>nginx</center>` page is served instead. Body must be "
            f"non-empty. Got: {body!r}"
        )
        assert re.search(r'return\s+404\s+"Not Found\\n"\s*;', body), (
            f'Scanner-block {label!r} must `return 404 "Not Found\\n";` — '
            f"non-empty body so nginx does not fall back to its default "
            f"error page. Got: {body!r}"
        )

    @pytest.mark.parametrize("label,block_regex", BLOCK_SIGNATURES)
    def test_block_includes_security_headers(self, nginx_config, label, block_regex):
        block_match = re.search(block_regex, nginx_config, re.DOTALL)
        assert block_match, f"Scanner-block location not found: {label}"
        body = block_match.group(1)
        assert "security-headers.conf" in body, (
            f"Scanner-block {label!r} must `include /etc/nginx/security-headers.conf` "
            f"so the explicit-body 404 still carries HSTS/CSP/nosniff/etc. Got: {body!r}"
        )


# Pentest round 6 defense-in-depth checks (scanner-prefix block, security.txt,
# robots.txt, 405 rewrite) live in `test_nginx_pentest_round6.py`.
#
# Production entrypoint script security checks live in `test_entrypoint_security.py`.
#
# Both were split out to keep this file under the constitutional 500-line limit.
