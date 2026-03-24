"""Security-critical email privacy tests (T051-T054)."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test import Client


@pytest.fixture
def public_mode(settings):
    settings.AUTH_MODE = "public"


def _register(client, username="privtest", email="secret@private.com"):
    return client.post(
        "/api/auth/register/",
        data=json.dumps({
            "username": username, "password": "StrongPass123!",
            "password_confirm": "StrongPass123!", "email": email, "privacy_accepted": True,
        }),
        content_type="application/json",
    )


@pytest.mark.django_db
class TestEmailNeverStored:

    @patch("apps.core.auth_api.send_verification_email")
    def test_email_not_in_user_table(self, mock_email, client, public_mode):
        """T051: After registration, auth_user.email is empty string."""
        _register(client)
        assert User.objects.get(username="privtest").email == ""

    @patch("apps.core.auth_api.send_verification_email")
    def test_email_not_in_raw_db(self, mock_email, client, public_mode):
        """T051 extended: Raw DB query confirms no email stored."""
        _register(client, username="rawtest", email="rawcheck@test.com")
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM auth_user WHERE username = %s", ["rawtest"])
            assert cursor.fetchone()[0] == ""

    @patch("apps.core.auth_api.send_verification_email")
    def test_email_sent_correctly(self, mock_email, client, public_mode):
        """T053: Email was sent to the right address."""
        _register(client, username="emailtest", email="verify@test.com")
        mock_email.assert_called_once()
        assert mock_email.call_args[0][1] == "verify@test.com"

    @patch("apps.core.auth_api.send_verification_email")
    def test_email_not_in_logs(self, mock_email, client, public_mode):
        """T054: Log output does NOT contain the email."""
        with patch("apps.core.auth_api.security_logger") as mock_logger:
            _register(client, username="logtest", email="nologme@secret.com")
            for call in mock_logger.method_calls:
                for arg in call.args:
                    if isinstance(arg, str):
                        assert "nologme@secret.com" not in arg
