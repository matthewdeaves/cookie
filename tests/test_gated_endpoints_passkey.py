"""Integration tests for the 18 gated admin endpoints in passkey mode.

Every endpoint MUST return 404 {"detail": "Not found"} regardless of caller
identity (anonymous, authenticated non-admin, authenticated admin), AND
`security_logger` MUST NOT gain any auth-failure log line during the probe.
"""

from __future__ import annotations

import json
import logging

import pytest
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.models import User
from django.test import Client

from apps.profiles.models import Profile
from apps.recipes.models import SearchSource


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


@pytest.fixture
def security_log(caplog):
    """Attach caplog's handler to the `security` logger (which sets propagate=False).

    Without this, `caplog.records` never sees security-logger output and the
    "no auth-failure log line" assertions pass trivially.
    """
    sec = logging.getLogger("security")
    sec.addHandler(caplog.handler)
    sec.setLevel(logging.WARNING)
    try:
        yield caplog
    finally:
        sec.removeHandler(caplog.handler)


@pytest.fixture
def source(db):
    return SearchSource.objects.create(
        host="example.com",
        name="Example",
        search_url_template="https://example.com/search?q={query}",
        result_selector=".recipe-card",
    )


def _create_user(username: str, is_staff: bool = False) -> User:
    user = User.objects.create_user(username=username, password="!", email="", is_active=True, is_staff=is_staff)
    user.set_unusable_password()
    user.save()
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


def _login_passkey(client: Client, user: User) -> None:
    """Authenticate via a real Django auth session (passkey-style)."""
    client.get("/api/system/health/")
    session = client.session
    session[SESSION_KEY] = str(user.pk)
    session[BACKEND_SESSION_KEY] = "django.contrib.auth.backends.ModelBackend"
    session[HASH_SESSION_KEY] = user.get_session_auth_hash()
    session["profile_id"] = user.profile.id
    session.save()


# Each entry: (method, path_fn(source_id, profile_id), body, label)
# path_fn is a callable so we can interpolate test IDs at probe time.
def _endpoints(source_id: int, profile_id: int) -> list[tuple[str, str, dict | None, str]]:
    return [
        ("POST", "/api/ai/save-api-key", {"api_key": "x"}, "save-api-key"),
        ("POST", "/api/ai/test-api-key", {"api_key": "x"}, "test-api-key"),
        ("GET", "/api/ai/prompts", None, "prompts-list"),
        ("GET", "/api/ai/prompts/tips_generation", None, "prompts-show"),
        ("PUT", "/api/ai/prompts/tips_generation", {"system_prompt": "x"}, "prompts-update"),
        ("POST", "/api/ai/repair-selector", {"source_id": source_id}, "repair-selector"),
        ("GET", "/api/ai/sources-needing-attention", None, "sources-needing-attention"),
        (
            "PUT",
            "/api/ai/quotas",
            {"remix": 99, "remix_suggestions": 99, "scale": 99, "tips": 99, "discover": 99, "timer": 99},
            "quotas",
        ),
        ("GET", "/api/system/reset-preview/", None, "reset-preview"),
        ("POST", "/api/system/reset/", {"confirmation_text": "RESET"}, "reset"),
        ("POST", f"/api/sources/{source_id}/toggle/", None, "source-toggle"),
        ("POST", "/api/sources/bulk-toggle/", {"enable": False}, "bulk-toggle"),
        ("PUT", f"/api/sources/{source_id}/selector/", {"result_selector": ".x"}, "source-selector"),
        ("POST", f"/api/sources/{source_id}/test/", None, "source-test"),
        ("POST", "/api/sources/test-all/", None, "sources-test-all"),
        ("GET", "/api/recipes/cache/health/", None, "cache-health"),
        ("POST", f"/api/profiles/{profile_id}/set-unlimited/", {"unlimited": True}, "profile-set-unlimited"),
        ("PATCH", f"/api/profiles/{profile_id}/rename/", {"name": "x"}, "profile-rename"),
    ]


def _probe(client: Client, method: str, path: str, body: dict | None):
    # Use method-specific helpers so Django's test client dispatches correctly;
    # client.generic() loses method on some async-capable routes.
    kwargs: dict = {}
    if body is not None:
        kwargs["data"] = json.dumps(body)
        kwargs["content_type"] = "application/json"
    return getattr(client, method.lower())(path, **kwargs)


@pytest.mark.django_db
class TestGatedEndpointsReturn404InPasskeyMode:
    """Every gated endpoint returns 404 in passkey mode for every caller identity."""

    @pytest.mark.parametrize("method,path,body,label", _endpoints(9999, 9999))
    def test_anonymous_probe_404(self, client, passkey_mode, method, path, body, label, security_log):
        response = _probe(client, method, path, body)
        assert response.status_code == 404, f"{label}: expected 404, got {response.status_code}"
        assert response.json() == {"detail": "Not found"}
        assert not any(
            "Admin auth failure" in r.getMessage() or "Auth failure" in r.getMessage() for r in security_log.records
        ), f"{label}: security log leaked an auth-failure line"

    def test_non_admin_probe_404(self, client, passkey_mode, source, security_log):
        regular = _create_user("regular_user")
        _login_passkey(client, regular)
        security_log.clear()  # discard the "no profile_id in session" lines from login setup
        for method, path, body, label in _endpoints(source.id, regular.profile.id):
            response = _probe(client, method, path, body)
            assert response.status_code == 404, f"{label}: expected 404, got {response.status_code} (non-admin)"
            assert response.json() == {"detail": "Not found"}, f"{label}: wrong body"
        # Gated endpoints MUST NOT contribute any admin-auth-failure lines.
        leaked = [r for r in security_log.records if "Admin auth failure" in r.getMessage()]
        assert not leaked, f"Admin auth failures leaked: {[r.getMessage() for r in leaked]}"

    def test_admin_probe_404(self, client, passkey_mode, source, security_log):
        admin = _create_user("admin_user", is_staff=True)
        _login_passkey(client, admin)
        security_log.clear()
        for method, path, body, label in _endpoints(source.id, admin.profile.id):
            response = _probe(client, method, path, body)
            assert response.status_code == 404, f"{label}: expected 404, got {response.status_code} (admin)"
            assert response.json() == {"detail": "Not found"}, f"{label}: wrong body"
        leaked = [r for r in security_log.records if "Admin auth failure" in r.getMessage()]
        assert not leaked, f"Admin auth failures leaked: {[r.getMessage() for r in leaked]}"


# Paths to probe for the method-gate test: cover one example of each Ninja
# route shape that uses HomeOnlyAuth, including every Profile verb from the
# v1.43.0 move. All must 404 on every verb — no Allow header may leak the
# registered method set (pentest finding, v1.45.0).
_ALL_VERBS = ("GET", "HEAD", "OPTIONS", "POST", "PUT", "DELETE", "PATCH")
# `/api/ai/quotas` is intentionally excluded: GET uses SessionAuth (any mode),
# only PUT is HomeOnlyAuth — the path must stay reachable for GET in passkey
# mode, so it is not a candidate for the "every verb is 404" invariant.
_HOME_ONLY_PROBE_PATHS = (
    "/api/profiles/1/",
    "/api/profiles/1/deletion-preview/",
    "/api/profiles/1/set-unlimited/",
    "/api/profiles/1/rename/",
    "/api/ai/save-api-key",
    "/api/ai/prompts",
    "/api/ai/prompts/tips_generation",
    "/api/ai/sources-needing-attention",
    "/api/ai/repair-selector",
    "/api/sources/bulk-toggle/",
    "/api/sources/test-all/",
    "/api/sources/1/toggle/",
    "/api/sources/1/selector/",
    "/api/sources/1/test/",
    "/api/recipes/cache/health/",
    "/api/system/reset-preview/",
    "/api/system/reset/",
)


@pytest.mark.django_db
class TestHomeOnlyRoutesHaveNoMethodLeak:
    """Every verb on a HomeOnlyAuth route returns 404 with no Allow header in
    passkey mode. Guards against Django's 405 Method-Not-Allowed handler
    leaking the registered method set on HEAD/OPTIONS probes (pentest r3)."""

    @pytest.mark.parametrize("path", _HOME_ONLY_PROBE_PATHS)
    @pytest.mark.parametrize("verb", _ALL_VERBS)
    def test_every_verb_404_no_allow_header(self, client, passkey_mode, path, verb):
        response = client.generic(verb, path)
        assert response.status_code == 404, f"{verb} {path}: expected 404, got {response.status_code}"
        assert "Allow" not in response.headers, (
            f"{verb} {path}: Allow header leaked route existence ({response.headers.get('Allow')!r})"
        )
