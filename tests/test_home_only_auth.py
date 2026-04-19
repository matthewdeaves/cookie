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

from apps.core.auth import HomeOnlyAuth, SessionAuth


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
