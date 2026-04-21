"""
Runtime integration tests for the nginx scanner-block behaviour.

Why this file exists
--------------------
`tests/test_nginx_security.py` only reads ``nginx.prod.conf`` as text and
asserts the presence of specific directives. That kind of static check could
NOT detect pentest round 6 / F-1: the literal directive ``return 404 "";`` is
a nginx no-op — a zero-length body is silently dropped and the HTTP core
falls back to the default error page, which re-exposes the stock
``<center>nginx</center>`` footer. The config "looked right" to every
string-based assertion, but the live response still leaked the proxy
identity on ~20 scanner probe paths. v1.46.0 and v1.47.0 both shipped this
broken pattern.

The only way to catch that class of bug is to run nginx and inspect actual
response bodies. This module does exactly that: it spins up ``nginx:alpine``
with a config that mirrors the production scanner-block directives, then
asserts that no response body for a scanner probe path contains the string
``"nginx"``.

The test is skipped gracefully when docker is not available (e.g. when
running ``pytest`` inside the ``web`` container without mounting the docker
socket). It runs on GitHub Actions ``ubuntu-latest``, where docker is
available by default.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import requests

# Shared helpers (docker_required marker, NGINX_TEST_CONFIG, nginx_base_url
# fixture) live in tests/conftest.py so multiple test files can reuse them
# without blowing past the 500-line file cap.
from tests.conftest import NGINX_TEST_CONFIG, docker_required  # noqa: F401


# Probe paths representative of each scanner block. Matches the paths the
# pentest round-6 handoff called out as leaking the stock nginx page in
# production against v1.47.0.
SCANNER_PATHS = [
    # Dotfile block
    "/.env",
    "/.git/config",
    "/.htaccess",
    # Sensitive-extension block
    "/config.php.bak",
    "/backup.sql",
    "/sitemap.xml",
    "/wp-login.php",
    "/xmlrpc.php",
    "/admin.php",
    "/vendor/phpunit/phpunit/src/Util/PHP/eval-stdin.php",
    # Sourcemap block
    "/bundle.js.map",
    # Specific-filename block
    "/server-status",
    "/manage.py",
    "/Dockerfile",
    "/apple-app-site-association",
    # Scanner-prefix block (pentest round 6 / F-4)
    "/admin",
    "/admin/",
    "/wp-admin/",
    "/phpmyadmin/",
    "/actuator/env",
    "/dashboard/",
    "/metrics",
    # Catch-all (exercises @not_found via error_page)
    "/does-not-exist",
]


# Pentest round 7 / F-18: extended framework-probe paths. In v1.48.0 these
# fell through to the SPA catch-all and returned the Cookie index.html at 200.
SCANNER_PATHS_EXTENDED = [
    "/console",
    "/administrator",
    "/_profiler",
    "/env",
    "/health",
    "/status",
    "/api_docs",
    "/graphql",
    "/solr/",
    "/jenkins/",
    "/cgi-bin/",
    "/cgi-bin/test.cgi",
    "/LICENSE",
    "/README.md",
    "/CHANGELOG.md",
    "/HEAD",
    "/Gemfile.lock",
    "/package-lock.json",
    "/yarn.lock",
    "/composer.lock",
    "/web.config",
    "/server-info",
]


@docker_required
@pytest.mark.parametrize("path", SCANNER_PATHS)
def test_scanner_block_body_does_not_leak_nginx(nginx_base_url, path):
    """Response body must not contain the substring "nginx" (case-insensitive).

    Regression guard for pentest round 6 / F-1: `return 404 "";` silently
    serves the default nginx error page whose body contains
    `<center>nginx</center>`. Any non-empty body literal (e.g.
    `"Not Found\n"`) suppresses that fallback.
    """
    response = requests.get(f"{nginx_base_url}{path}", timeout=2.0)
    assert response.status_code == 404, (
        f"{path}: expected 404, got {response.status_code}. Body: {response.text!r}"
    )
    assert "nginx" not in response.text.lower(), (
        f"{path} leaked proxy-identity body: {response.text[:200]!r}. "
        "This is the pentest round 6 / F-1 regression — a scanner-block "
        "location is serving the default nginx error page. Check that the "
        "corresponding `return 404 ...;` directive in nginx.prod.conf has a "
        "non-empty body literal; an empty string is a no-op."
    )


@docker_required
def test_scanner_block_body_is_expected_content(nginx_base_url):
    """Sanity-check that the body is exactly what the config says it is."""
    response = requests.get(f"{nginx_base_url}/.env", timeout=2.0)
    assert response.status_code == 404
    assert response.text == "Not Found\n"
    # Status sanity — default_type is text/plain, not the stock text/html.
    assert response.headers["content-type"].startswith("text/plain")


@docker_required
def test_security_txt_is_rfc_9116(nginx_base_url):
    """Pentest round 6 / F-15: /.well-known/security.txt serves a real
    text/plain RFC 9116 body, not the SPA homepage."""
    response = requests.get(f"{nginx_base_url}/.well-known/security.txt", timeout=2.0)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "Contact: mailto:" in body
    assert "Expires:" in body
    # No nginx leak on this path either.
    assert "nginx" not in body.lower()


@docker_required
def test_robots_txt_disallows_all(nginx_base_url):
    """Pentest round 6 / F-4: /robots.txt serves a real text/plain body,
    not the SPA homepage."""
    response = requests.get(f"{nginx_base_url}/robots.txt", timeout=2.0)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "User-agent: *" in response.text
    assert "Disallow: /" in response.text


@docker_required
@pytest.mark.parametrize("body", [b'{"bad":', b"not json at all", b""])
def test_api_probe_with_malformed_body_does_not_leak_nginx(nginx_base_url, body):
    """Pentest round 6 / F-16: POST to an /api/ path with an unparseable
    body used to hit `return 404 "";` somewhere in the stack and leak the
    stock nginx 404 page. In this standalone nginx config there's no
    /api/ proxy, so the request falls through to the catch-all `location /`
    → @not_found handler. That path must not leak either."""
    response = requests.post(
        f"{nginx_base_url}/api/profiles/",
        data=body,
        headers={"Content-Type": "application/json"},
        timeout=2.0,
    )
    assert "nginx" not in response.text.lower(), (
        f"/api/profiles/ with malformed body leaked nginx: {response.text[:200]!r}"
    )


@docker_required
@pytest.mark.parametrize("path", SCANNER_PATHS_EXTENDED)
def test_extended_scanner_probes_are_404_not_spa(nginx_base_url, path):
    """Pentest round 7 / F-18: framework-fingerprint probes (`/console`,
    `/env`, `/graphql`, etc.) must 404 with a plain-text body, not fall
    through to an SPA catch-all that would otherwise return the React
    homepage with a 200.

    Regression class: the round-6 F-4 scanner-prefix block covered CMS-style
    paths (wp-*, phpmyadmin, actuator, …) but not tool/framework paths.
    Scanners fingerprint apps off `/env` and `/health` just as readily as
    `/wp-login.php`, so both classes need blocking.
    """
    response = requests.get(f"{nginx_base_url}{path}", timeout=2.0)
    assert response.status_code == 404, (
        f"{path}: expected 404, got {response.status_code}. "
        f"Body: {response.text[:200]!r}"
    )
    assert "nginx" not in response.text.lower(), (
        f"{path} leaked proxy identity: {response.text[:200]!r}"
    )
    # Explicit guard against SPA-title leakage — the v1.48.0 regression
    # symptom was a 200 with the Cookie SPA HTML. The title would survive
    # through here if someone accidentally removed the extended block.
    assert "Cookie - Recipe Manager" not in response.text, (
        f"{path} leaked SPA homepage (F-18 regression): {response.text[:200]!r}"
    )


@docker_required
def test_assets_bare_path_is_404_no_leak(nginx_base_url):
    """Pentest round 7 / F-19 (assets variant): bare `/assets` must 404 with
    a plain-text body. Legitimate Vite requests always include a hashed
    filename (`/assets/<file>.ext`); only scanners probe `/assets`.

    Before this fix, nginx's implicit directory-redirect on `/assets` →
    `/assets/` attached nginx's default HTML body (161 bytes containing
    `<center>nginx</center>`), re-introducing the F-1 class of proxy-
    identity leak on a 301 status.
    """
    response = requests.get(
        f"{nginx_base_url}/assets",
        timeout=2.0,
        allow_redirects=False,
    )
    assert response.status_code == 404, (
        f"/assets: expected 404, got {response.status_code}"
    )
    assert "nginx" not in response.text.lower(), (
        f"/assets leaked proxy identity: {response.text[:200]!r}"
    )


def test_production_config_mirrors_test_body_literal():
    """If the production body literal changes, this test file must change too.

    We can't `include` nginx.prod.conf from the test config (it references
    paths that only exist inside the built image), so we copy the
    `return 404 ...;` bodies. This test locks the two in sync — if someone
    edits the production literal without updating the runtime test, the
    test suite fails loudly.
    """
    prod_conf = (Path(__file__).parent.parent / "nginx" / "nginx.prod.conf").read_text()
    # Strip comment lines so the explanatory NOTE about `return 404 "";` in
    # @not_found doesn't trip the regression guard below.
    directive_lines = [
        line for line in prod_conf.splitlines()
        if not line.lstrip().startswith("#")
    ]
    directives = "\n".join(directive_lines)

    # The production config must use this exact body on every scanner-block
    # return. If you need to change the body, update NGINX_TEST_CONFIG above
    # and this assertion in the same commit.
    expected = 'return 404 "Not Found\\n";'
    occurrences = directives.count(expected)
    assert occurrences >= 5, (
        f"Expected >= 5 occurrences of {expected!r} in nginx.prod.conf "
        f"(outside comments), found {occurrences}. Either the production "
        f"config has regressed to an empty body (pentest round 6 / F-1) or "
        f"the body literal has been changed without updating "
        f"tests/test_nginx_runtime.py."
    )
    # Guard the reverse direction too: no `return 404 "";` should survive
    # in the production config's directives.
    assert 'return 404 "";' not in directives, (
        'nginx.prod.conf contains `return 404 "";` — this is a nginx no-op. '
        "The zero-length body is dropped and the default error page is served, "
        "leaking the `<center>nginx</center>` footer (pentest round 6 / F-1)."
    )
