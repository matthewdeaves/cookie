"""Unit tests for HomeOnlyAdminAuth — the mode-gated AdminAuth subclass."""

import logging
from unittest.mock import MagicMock, patch

import pytest
from django.test import RequestFactory, override_settings
from ninja.errors import HttpError

from apps.core.auth import AdminAuth, HomeOnlyAdminAuth


@pytest.fixture
def request_factory():
    return RequestFactory()


@override_settings(AUTH_MODE="passkey")
def test_passkey_mode_raises_404_before_auth(request_factory, caplog):
    """In passkey mode, HomeOnlyAdminAuth raises 404 before cookie extraction.

    AdminAuth.authenticate() MUST NOT run; no auth-failure log line MUST appear.
    """
    caplog.set_level(logging.WARNING, logger="security")
    auth = HomeOnlyAdminAuth()
    request = request_factory.get("/api/ai/save-api-key")

    with patch.object(AdminAuth, "authenticate") as mocked_authenticate:
        with pytest.raises(HttpError) as exc_info:
            auth(request)
        mocked_authenticate.assert_not_called()

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Not found"
    # No auth-failure security log line during the mode check
    assert not any(
        "Admin auth failure" in record.message or "Auth failure" in record.message
        for record in caplog.records
    )


@override_settings(AUTH_MODE="home")
def test_home_mode_delegates_to_adminauth(request_factory):
    """In home mode, HomeOnlyAdminAuth.__call__ delegates to AdminAuth.__call__."""
    auth = HomeOnlyAdminAuth()
    request = request_factory.get("/api/ai/save-api-key")

    sentinel = MagicMock(name="adminauth_result")
    with patch.object(AdminAuth, "__call__", return_value=sentinel) as mocked_call:
        result = auth(request)

    mocked_call.assert_called_once_with(request)
    assert result is sentinel


@override_settings(AUTH_MODE="unrecognised-value")
def test_unrecognised_mode_also_raises_404(request_factory):
    """Any value other than 'home' produces 404 (defensive default)."""
    auth = HomeOnlyAdminAuth()
    request = request_factory.get("/api/ai/save-api-key")

    with pytest.raises(HttpError) as exc_info:
        auth(request)

    assert exc_info.value.status_code == 404
    assert exc_info.value.message == "Not found"
