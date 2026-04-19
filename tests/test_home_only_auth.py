"""Unit tests for HomeOnlyAuth — the mode-gated SessionAuth subclass.

HomeOnlyAuth replaces the pre-v1.43.0 pair (AdminAuth + HomeOnlyAdminAuth)
after admin privilege was retired from the auth layer
(spec 014-remove-is-staff).
"""

import logging
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory, override_settings
from ninja.errors import HttpError

from apps.core.auth import HomeOnlyAnonAuth, HomeOnlyAuth, SessionAuth


@pytest.fixture
def request_factory():
    return RequestFactory()


@override_settings(AUTH_MODE="passkey")
def test_passkey_mode_raises_404_before_auth(request_factory, caplog):
    """In passkey mode, HomeOnlyAuth raises 404 before cookie extraction.

    SessionAuth.__call__ MUST NOT run; no auth-failure log line MUST appear.
    """
    caplog.set_level(logging.WARNING, logger="security")
    auth = HomeOnlyAuth()
    request = request_factory.get("/api/ai/save-api-key")

    with patch.object(SessionAuth, "__call__") as mocked_call:
        with pytest.raises(HttpError) as exc_info:
            auth(request)
        mocked_call.assert_not_called()

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Not found"
    # No auth-failure security log line during the mode check
    assert not any(
        "Admin auth failure" in record.message or "Auth failure" in record.message for record in caplog.records
    )


@override_settings(AUTH_MODE="home")
def test_home_mode_delegates_to_sessionauth(request_factory):
    """In home mode, HomeOnlyAuth.__call__ delegates to SessionAuth.__call__."""
    auth = HomeOnlyAuth()
    request = request_factory.get("/api/ai/save-api-key")

    sentinel = MagicMock(name="sessionauth_result")
    with patch.object(SessionAuth, "__call__", return_value=sentinel) as mocked_call:
        result = auth(request)

    mocked_call.assert_called_once_with(request)
    assert result is sentinel


@override_settings(AUTH_MODE="unrecognised-value")
def test_unrecognised_mode_also_raises_404(request_factory):
    """Any value other than 'home' produces 404 (defensive default)."""
    auth = HomeOnlyAuth()
    request = request_factory.get("/api/ai/save-api-key")

    with pytest.raises(HttpError) as exc_info:
        auth(request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Not found"


# ── HomeOnlyAnonAuth (pentest round 5 / F2) ──


@override_settings(AUTH_MODE="passkey")
def test_anon_auth_raises_404_in_passkey_mode(request_factory):
    """Pre-session variant still 404s in non-home modes, without session lookup."""
    auth = HomeOnlyAnonAuth()
    request = request_factory.get("/api/profiles/")

    with pytest.raises(HttpError) as exc_info:
        auth(request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Not found"


@override_settings(AUTH_MODE="home")
def test_anon_auth_home_mode_allows_anonymous_get(request_factory):
    """Home mode: safe methods bypass CSRF check and return truthy (no session required)."""
    auth = HomeOnlyAnonAuth()
    request = request_factory.get("/api/profiles/")

    result = auth(request)

    assert result is True


@override_settings(AUTH_MODE="home")
def test_anon_auth_is_instance_of_home_only_auth():
    """Inheritance is required so HomeOnlyRouteGateMiddleware includes these
    paths in the route-gate introspection (any op that uses HomeOnlyAnonAuth
    counts as HomeOnlyAuth for middleware purposes)."""
    assert isinstance(HomeOnlyAnonAuth(), HomeOnlyAuth)
