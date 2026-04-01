"""Tests for device code authorization flow API (apps/core/device_code_api.py)."""

import json
from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client
from django.utils import timezone

from apps.core.models import DeviceCode
from apps.profiles.models import Profile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_with_profile(db):
    """Create a Django user with an associated profile."""
    user = User.objects.create_user(username="testuser", password="testpass123")
    profile = Profile.objects.create(user=user, name="Test User", avatar_color="#d97850")
    return user, profile


@pytest.fixture
def auth_client(client, user_with_profile):
    """Return a client authenticated in passkey mode (session has profile_id and user is logged in)."""
    user, profile = user_with_profile
    client.force_login(user)
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PASSKEY_MODE = patch("django.conf.settings.AUTH_MODE", "passkey")
HOME_MODE = patch("django.conf.settings.AUTH_MODE", "home")

CODE_URL = "/api/auth/device/code/"
POLL_URL = "/api/auth/device/poll/"
AUTHORIZE_URL = "/api/auth/device/authorize/"


def _make_device_code(session_key, **kwargs):
    """Create a DeviceCode with sensible defaults."""
    defaults = {
        "code": "ABC123",
        "session_key": session_key,
        "status": "pending",
        "attempts_remaining": 5,
        "expires_at": timezone.now() + timedelta(seconds=600),
    }
    defaults.update(kwargs)
    return DeviceCode.objects.create(**defaults)


# ===========================================================================
# Tests: Non-passkey mode returns 404
# ===========================================================================


@pytest.mark.django_db
class TestNonPasskeyMode:
    """All device code endpoints should 404 when AUTH_MODE is not 'passkey'."""

    def test_request_code_404_in_home_mode(self, client):
        with HOME_MODE:
            resp = client.post(CODE_URL, content_type="application/json")
        assert resp.status_code == 404

    def test_poll_status_404_in_home_mode(self, client):
        with HOME_MODE:
            resp = client.get(POLL_URL)
        assert resp.status_code == 404

    def test_authorize_code_404_in_home_mode(self, auth_client):
        with HOME_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        # 404 because passkey mode check happens before auth in the view
        assert resp.status_code == 404


# ===========================================================================
# Tests: request_code endpoint (POST /code/)
# ===========================================================================


@pytest.mark.django_db
class TestRequestCode:
    """POST /api/auth/device/code/ - generate a new device pairing code."""

    def test_success_returns_201(self, client):
        with PASSKEY_MODE:
            resp = client.post(CODE_URL, content_type="application/json")
        assert resp.status_code == 201
        data = resp.json()
        assert "code" in data
        assert len(data["code"]) == 6
        assert "expires_in" in data
        assert data["poll_interval"] == 5
        assert data["poll_url"] == "/api/auth/device/poll/"

    def test_creates_device_code_in_db(self, client):
        with PASSKEY_MODE:
            resp = client.post(CODE_URL, content_type="application/json")
        assert resp.status_code == 201
        code_str = resp.json()["code"]
        assert DeviceCode.objects.filter(code=code_str, status="pending").exists()

    def test_invalidates_old_pending_codes(self, client):
        """Requesting a new code should invalidate existing pending/authorized codes for the session."""
        with PASSKEY_MODE:
            # First request to establish session
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            code1 = resp1.json()["code"]

            # Second request should invalidate the first
            resp2 = client.post(CODE_URL, content_type="application/json")
            assert resp2.status_code == 201
            code2 = resp2.json()["code"]

        assert code1 != code2
        old_code = DeviceCode.objects.get(code=code1)
        assert old_code.status == "invalidated"

    def test_invalidates_old_authorized_codes(self, client, user_with_profile):
        """Authorized codes for the same session are also invalidated."""
        user, _ = user_with_profile
        with PASSKEY_MODE:
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            code1 = resp1.json()["code"]

            # Manually mark as authorized
            dc = DeviceCode.objects.get(code=code1)
            dc.status = "authorized"
            dc.authorizing_user = user
            dc.save()

            # Request another code
            resp2 = client.post(CODE_URL, content_type="application/json")
            assert resp2.status_code == 201

        dc.refresh_from_db()
        assert dc.status == "invalidated"

    def test_session_created_if_missing(self, client):
        """If the client has no session, one is created."""
        with PASSKEY_MODE:
            resp = client.post(CODE_URL, content_type="application/json")
        assert resp.status_code == 201
        # Session should now exist
        assert client.session.session_key is not None

    def test_integrity_error_retry(self, client):
        """If code generation hits IntegrityError, it retries."""
        from django.db import IntegrityError

        call_count = 0
        original_create = DeviceCode.objects.create

        def flaky_create(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise IntegrityError("duplicate key")
            return original_create(**kwargs)

        with PASSKEY_MODE:
            with patch.object(DeviceCode.objects, "create", side_effect=flaky_create):
                resp = client.post(CODE_URL, content_type="application/json")

        assert resp.status_code == 201
        assert call_count == 2

    def test_all_retries_exhausted_returns_429(self, client):
        """If all 10 retry attempts fail with IntegrityError, returns 429."""
        from django.db import IntegrityError

        with PASSKEY_MODE:
            with patch.object(
                DeviceCode.objects,
                "create",
                side_effect=IntegrityError("duplicate key"),
            ):
                resp = client.post(CODE_URL, content_type="application/json")

        assert resp.status_code == 429
        assert "Unable to generate code" in resp.json()["error"]

    def test_cleans_up_expired_codes(self, client):
        """Expired non-authorized codes for the session are deleted."""
        with PASSKEY_MODE:
            # First create a code to establish session
            resp = client.post(CODE_URL, content_type="application/json")
            assert resp.status_code == 201
            session_key = client.session.session_key

            # Manually create an expired code for this session
            expired = DeviceCode.objects.create(
                code="EXP001",
                session_key=session_key,
                status="expired",
                attempts_remaining=5,
                expires_at=timezone.now() - timedelta(seconds=1),
            )
            # Also invalidate the first code so it's not "pending"
            DeviceCode.objects.filter(session_key=session_key, status="pending").update(status="invalidated")

            # Request new code -- should clean up expired
            resp2 = client.post(CODE_URL, content_type="application/json")
            assert resp2.status_code == 201

        assert not DeviceCode.objects.filter(pk=expired.pk).exists()


# ===========================================================================
# Tests: poll_status endpoint (GET /poll/)
# ===========================================================================


@pytest.mark.django_db
class TestPollStatus:
    """GET /api/auth/device/poll/ - poll for device code authorization status."""

    def test_no_session_returns_410(self, client):
        """No session key at all returns 410."""
        with PASSKEY_MODE:
            resp = client.get(POLL_URL)
        assert resp.status_code == 410
        data = resp.json()
        assert data["status"] == "expired"
        assert "No active code" in data["error"]

    def test_no_active_code_returns_410(self, client):
        """Session exists but no active device code returns 410."""
        with PASSKEY_MODE:
            # Force session creation
            session = client.session
            session["dummy"] = "value"
            session.save()
            resp = client.get(POLL_URL)
        assert resp.status_code == 410
        data = resp.json()
        assert data["status"] == "expired"

    def test_pending_code_returns_202(self, client):
        """Pending, non-expired code returns 202."""
        with PASSKEY_MODE:
            # Request a code first to create session + code
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201

            resp = client.get(POLL_URL)
        assert resp.status_code == 202
        assert resp.json()["status"] == "pending"

    def test_expired_code_returns_410(self, client):
        """An expired pending code returns 410 and gets marked expired."""
        with PASSKEY_MODE:
            # Create a code
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            code_str = resp1.json()["code"]

            # Manually expire it
            dc = DeviceCode.objects.get(code=code_str)
            dc.expires_at = timezone.now() - timedelta(seconds=1)
            dc.save(update_fields=["expires_at"])

            resp = client.get(POLL_URL)
        assert resp.status_code == 410
        data = resp.json()
        assert data["status"] == "expired"
        assert "expired" in data["error"].lower()

        dc.refresh_from_db()
        assert dc.status == "expired"

    def test_authorized_code_logs_in_user(self, client, user_with_profile):
        """An authorized code with a valid user returns 200 and logs in the user."""
        user, profile = user_with_profile
        with PASSKEY_MODE:
            # Create a code
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            code_str = resp1.json()["code"]

            # Authorize it
            dc = DeviceCode.objects.get(code=code_str)
            dc.status = "authorized"
            dc.authorizing_user = user
            dc.save(update_fields=["status", "authorizing_user"])

            resp = client.get(POLL_URL)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "authorized"
        assert data["user"]["id"] == user.id
        assert data["profile"]["id"] == profile.id
        assert data["profile"]["name"] == profile.name

        # Code should now be consumed (expired)
        dc.refresh_from_db()
        assert dc.status == "expired"

    def test_authorized_code_no_user_returns_410(self, client):
        """Authorized code where authorizing_user is None returns 410."""
        with PASSKEY_MODE:
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            code_str = resp1.json()["code"]

            dc = DeviceCode.objects.get(code=code_str)
            dc.status = "authorized"
            dc.authorizing_user = None
            dc.save(update_fields=["status", "authorizing_user"])

            resp = client.get(POLL_URL)
        assert resp.status_code == 410
        data = resp.json()
        assert data["status"] == "expired"
        assert "invalid" in data["error"].lower()

        dc.refresh_from_db()
        assert dc.status == "invalidated"

    def test_polls_most_recent_code(self, client):
        """When multiple codes exist, poll returns the most recent one."""
        with PASSKEY_MODE:
            resp1 = client.post(CODE_URL, content_type="application/json")
            assert resp1.status_code == 201
            # The first code gets invalidated by the second request
            resp2 = client.post(CODE_URL, content_type="application/json")
            assert resp2.status_code == 201

            # Poll should find the second (pending) code
            resp = client.get(POLL_URL)
        assert resp.status_code == 202
        assert resp.json()["status"] == "pending"


# ===========================================================================
# Tests: authorize_code endpoint (POST /authorize/)
# ===========================================================================


@pytest.mark.django_db
class TestAuthorizeCode:
    """POST /api/auth/device/authorize/ - authorize a pending device code."""

    def test_requires_authentication(self, client):
        """Unauthenticated request returns 401."""
        with PASSKEY_MODE:
            resp = client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 401

    def test_authorize_valid_code(self, auth_client, user_with_profile):
        """Authorizing a valid pending code returns 200."""
        user, _ = user_with_profile
        # Create a pending code from a different session
        dc = _make_device_code("othersession1234567890123456789012")

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        assert resp.json()["message"] == "Device authorized"

        dc.refresh_from_db()
        assert dc.status == "authorized"
        assert dc.authorizing_user == user

    def test_authorize_normalizes_code(self, auth_client, user_with_profile):
        """Code is stripped and uppercased before lookup."""
        _make_device_code("othersession1234567890123456789012")

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "  abc123  "}),
                content_type="application/json",
            )
        assert resp.status_code == 200

    def test_invalid_code_returns_400(self, auth_client):
        """Non-existent code returns 400."""
        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "XXXXXX"}),
                content_type="application/json",
            )
        assert resp.status_code == 400
        assert "Invalid or expired" in resp.json()["error"]

    def test_expired_code_returns_400(self, auth_client):
        """Expired code returns 400 and gets marked expired."""
        dc = _make_device_code(
            "othersession1234567890123456789012",
            expires_at=timezone.now() - timedelta(seconds=1),
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 400
        assert "Invalid or expired" in resp.json()["error"]

        dc.refresh_from_db()
        assert dc.status == "expired"

    def test_already_authorized_code_returns_400(self, auth_client, user_with_profile):
        """An already authorized code is not found (filter is status=pending)."""
        user, _ = user_with_profile
        _make_device_code(
            "othersession1234567890123456789012",
            status="authorized",
            authorizing_user=user,
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_already_expired_status_code_returns_400(self, auth_client):
        """A code with status='expired' is not found."""
        _make_device_code(
            "othersession1234567890123456789012",
            status="expired",
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_invalidated_code_returns_400(self, auth_client):
        """A code with status='invalidated' is not found."""
        _make_device_code(
            "othersession1234567890123456789012",
            status="invalidated",
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 400

    def test_authorize_decrements_attempts_remaining(self, auth_client):
        """Each authorize attempt decrements attempts_remaining."""
        dc = _make_device_code("othersession1234567890123456789012", attempts_remaining=5)

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ABC123"}),
                content_type="application/json",
            )
        assert resp.status_code == 200
        dc.refresh_from_db()
        assert dc.attempts_remaining == 4

    def test_code_invalidated_at_zero_attempts(self, auth_client):
        """Code with 1 attempt left is invalidated after use."""
        dc = _make_device_code(
            "othersession1234567890123456789012",
            code="ZZZ999",
            attempts_remaining=1,
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "ZZZ999"}),
                content_type="application/json",
            )
        # Attempt is consumed, reaching 0 — code invalidated
        assert resp.status_code == 400
        assert "too many attempts" in resp.json()["error"].lower()
        dc.refresh_from_db()
        assert dc.status == "invalidated"
        assert dc.attempts_remaining == 0

    def test_already_exhausted_code_returns_400(self, auth_client):
        """Code with 0 attempts remaining is immediately rejected."""
        dc = _make_device_code(
            "othersession1234567890123456789012",
            code="EXH000",
            attempts_remaining=0,
        )

        with PASSKEY_MODE:
            resp = auth_client.post(
                AUTHORIZE_URL,
                data=json.dumps({"code": "EXH000"}),
                content_type="application/json",
            )
        assert resp.status_code == 400
        assert "too many attempts" in resp.json()["error"].lower()
        dc.refresh_from_db()
        assert dc.status == "invalidated"
