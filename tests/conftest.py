"""
Pytest configuration for Cookie tests.

Ensures proper test isolation, especially for async tests that use AsyncClient.
Also provides shared nginx runtime-test fixtures used by the round-7, round-10,
and runtime nginx test files.
"""

import shutil
import socket
import subprocess
import time

import pytest
import requests

# --- Test isolation -------------------------------------------------------


@pytest.fixture(autouse=True)
def _clear_cached_search_images(db):
    """
    Clean up CachedSearchImage table before each test.

    CachedSearchImage is a cache table that can accumulate entries across tests
    when async tests use connections outside the test transaction. This fixture
    ensures each test starts with a clean cache table.

    The cleanup is fast (milliseconds) and ensures reliable test isolation.
    """
    from apps.recipes.models import CachedSearchImage

    CachedSearchImage.objects.all().delete()
    yield
    # No cleanup needed after - each test gets a fresh transaction anyway


# --- Shared nginx fixtures for runtime scanner-block tests ----------------
#
# These live in conftest.py so multiple test files (test_nginx_runtime.py,
# test_nginx_pentest_round10.py, etc.) can share one nginx:alpine container
# and one copy of NGINX_TEST_CONFIG. That keeps every test file under the
# 500-line constitutional limit without losing regression coverage.

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
# it depends on /app/frontend/dist, /app/staticfiles, and the upstream Django
# service — none of which exist in nginx:alpine. The directives that MATTER
# for the F-1 behaviour (the `return 404 "...";` bodies) are copied verbatim
# below, so a regression in the production config's body literal would also
# manifest here if someone keeps the two in sync. The `return 404 "Not
# Found\n"` invariant is guarded by test_production_config_mirrors_test_body_literal
# in test_nginx_runtime.py.
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

        # Specific-filename block (extended in round 10 / F-27)
        location ~* ^/(Dockerfile|Makefile|Vagrantfile|Procfile|Gemfile|Rakefile|Thumbs\.db|requirements\.txt|Pipfile|manage\.py|server-status|server-info|crossdomain\.xml|clientaccesspolicy\.xml|apple-app-site-association|swagger\.json|manifest\.json|package\.json|composer\.json|tsconfig\.json|backup\.zip|backup\.tar|backup\.tar\.gz|backup\.sql|nginx_status)$ {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Scanner-prefix block (pentest round 6 / F-4)
        location ~* ^/(admin|wp-admin|wp-login|wp-includes|wp-content|wp-json|phpmyadmin|pma|myadmin|adminer|mysql|actuator|manager|jmx-console|axis2|Telerik\.Web\.UI|dashboard|metrics|ping|docs)($|/) {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # Extended scanner-prefix block (pentest round 7 / F-18, round 10 / F-27)
        location ~* ^/(console|administrator|_profiler|env|health|status|api_docs|api-docs|graphql|solr|jenkins|cgi-bin|server-info|HEAD|CHANGELOG\.md|LICENSE|README\.md|Gemfile\.lock|package-lock\.json|yarn\.lock|composer\.lock|web\.config|debug|_debug|__debug__|_debug_toolbar|debug-toolbar|traefik|prometheus|grafana|kibana|portainer|vendor|backup|backups|swagger|swagger-ui|swagger-resources|redoc|openapi)($|/) {
            default_type text/plain;
            return 404 "Not Found\n";
        }

        # F-19 (round 7): bare /assets must 404 (scanner bait, never a real
        # Vite request path). The prod-config /api and /privacy bare-path
        # fix is `proxy_pass http://django` so Django's APPEND_SLASH emits
        # the empty-body 301 — we cannot mirror that in this standalone
        # config (no Django upstream). Static-config tests in
        # test_nginx_pentest_round7.py lock the prod proxy_pass in place.
        location = /assets {
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
    """Start a throwaway nginx:alpine container; yield its base URL.

    Module-scoped so multiple tests in one file share a single container,
    but each test file gets a fresh container (isolation between modules).
    """
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
