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

import shutil
import socket
import subprocess
import time
from pathlib import Path

import pytest
import requests

# Resolve the docker binary once, at import time, so every subprocess call
# uses an absolute path (avoids ruff S607 "partial executable path").
_DOCKER_BIN = shutil.which("docker")


def _docker_available() -> bool:
    """True iff the docker CLI exists AND the daemon answers."""
    if _DOCKER_BIN is None:
        return False
    try:
        result = subprocess.run(
            [_DOCKER_BIN, "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0 and bool(result.stdout.strip())


docker_required = pytest.mark.skipif(
    not _docker_available(),
    reason="docker CLI / daemon not available — nginx runtime test skipped",
)


# Minimal standalone nginx config that mirrors the scanner-block directives
# from nginx/nginx.prod.conf. We cannot reuse nginx.prod.conf directly because
# it depends on /app/frontend/dist, /app/staticfiles, and the upstream
# Django service — none of which exist in nginx:alpine. The directives that
# MATTER for the F-1 behaviour (the `return 404 "...";` bodies) are copied
# verbatim below, so a regression in the production config's body literal
# would also manifest here if someone keeps the two in sync.
NGINX_TEST_CONFIG = r"""
events { worker_connections 1024; }
http {
    server_tokens off;
    server {
        listen 80 default_server;

        error_page 403 =404 @not_found;
        error_page 404 @not_found;
        error_page 405 =404 @not_found;

        location @not_found {
            internal;
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Dotfile block
        location ~ /\.(?!well-known) {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Sourcemap block
        location ~* \.map$ {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Sensitive-extension block
        location ~* \.(sql|sqlite3|bak|log|conf|cfg|ini|py|yaml|yml|toml|lock|sh|php|asp|jsp|pl|rb|xml)$ {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Specific-filename block
        location ~* ^/(Dockerfile|Makefile|Vagrantfile|Procfile|Gemfile|Rakefile|Thumbs\.db|requirements\.txt|Pipfile|manage\.py|server-status|server-info|crossdomain\.xml|clientaccesspolicy\.xml|apple-app-site-association|swagger\.json|manifest\.json)$ {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Scanner-prefix block (pentest round 6 / F-4)
        location ~* ^/(admin|wp-admin|wp-login|wp-includes|wp-content|wp-json|phpmyadmin|pma|myadmin|adminer|mysql|actuator|manager|jmx-console|axis2|Telerik\.Web\.UI|dashboard|metrics|ping|docs)($|/) {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # security.txt (pentest round 6 / F-15)
        location = /.well-known/security.txt {
            default_type text/plain;
            return 200 "Contact: mailto:hello@matthewdeaves.com\nPreferred-Languages: en\nExpires: 2027-04-20T00:00:00Z\n";
        }

        # robots.txt (pentest round 6 / F-4)
        location = /robots.txt {
            default_type text/plain;
            return 200 "User-agent: *\nDisallow: /\n";
        }

        # Catch-all — exercises @not_found via the server-level error_page.
        location / {
            return 404;
        }
    }
}
"""


def _free_port() -> int:
    """Ask the kernel for an unused TCP port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def nginx_base_url(tmp_path_factory):
    """Start a throwaway nginx:alpine container; yield its base URL."""
    conf_path = tmp_path_factory.mktemp("nginx") / "nginx.conf"
    conf_path.write_text(NGINX_TEST_CONFIG)

    container_name = "cookie-test-nginx-scanner-blocks"
    # Defensive: clear any stale container from a previous interrupted run.
    subprocess.run(
        [_DOCKER_BIN, "rm", "-f", container_name],
        capture_output=True,
        check=False,
    )

    port = _free_port()
    result = subprocess.run(
        [
            _DOCKER_BIN, "run", "-d", "--rm",
            "--name", container_name,
            "-p", f"127.0.0.1:{port}:80",
            "-v", f"{conf_path}:/etc/nginx/nginx.conf:ro",
            "nginx:alpine",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        pytest.skip(f"could not start nginx:alpine: {result.stderr.strip()}")

    base_url = f"http://127.0.0.1:{port}"
    try:
        # Wait up to 10s for nginx to accept connections.
        deadline = time.monotonic() + 10.0
        ready = False
        while time.monotonic() < deadline:
            try:
                requests.get(base_url, timeout=0.5)
                ready = True
                break
            except requests.RequestException:
                time.sleep(0.1)
        if not ready:
            logs = subprocess.run(
                [_DOCKER_BIN, "logs", container_name],
                capture_output=True, text=True,
            )
            pytest.fail(
                "nginx test container did not become ready within 10s. "
                f"stdout={logs.stdout!r} stderr={logs.stderr!r}"
            )
        yield base_url
    finally:
        subprocess.run(
            [_DOCKER_BIN, "rm", "-f", container_name],
            capture_output=True,
            check=False,
        )


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
