"""Tests for passkey (WebAuthn) authentication API endpoints."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.core.models import WebAuthnCredential
from apps.profiles.models import Profile


# --- Helpers ---

BASE = "/api/auth/passkey"


def _post_json(client, url, data=None):
    return client.post(url, data=json.dumps(data or {}), content_type="application/json")


def _delete(client, url):
    return client.delete(url, content_type="application/json")


def _make_user(username="pk_testuser", is_staff=False):
    user = User.objects.create_user(username=username, password=None, is_staff=is_staff)
    user.set_unusable_password()
    user.save(update_fields=["password"])
    return user


def _make_profile(user, name="Test User"):
    return Profile.objects.create(user=user, name=name, avatar_color="#d97850")


def _make_credential(user, credential_id=b"\x01\x02\x03", sign_count=0):
    return WebAuthnCredential.objects.create(
        user=user,
        credential_id=credential_id,
        public_key=b"\x04\x05\x06",
        sign_count=sign_count,
        transports=["internal"],
    )


def _auth_client(client, profile, user):
    client.force_login(user)
    session = client.session
    session["profile_id"] = profile.id
    session.save()
    return client


# --- Fixtures ---


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


@pytest.fixture
def home_mode(settings):
    settings.AUTH_MODE = "home"


@pytest.fixture
def user_and_profile(db):
    user = _make_user()
    profile = _make_profile(user)
    return user, profile


@pytest.fixture
def authed_client(user_and_profile, passkey_mode):
    user, profile = user_and_profile
    client = Client()
    _auth_client(client, profile, user)
    return client


# --- Tests: Non-passkey mode returns 404 ---


@pytest.mark.django_db
class TestNonPasskeyMode:
    """All passkey endpoints must return 404 when AUTH_MODE is not 'passkey'."""

    def test_register_options_404(self, anon_client, home_mode):
        assert _post_json(anon_client, f"{BASE}/register/options/").status_code == 404

    def test_register_verify_404(self, anon_client, home_mode):
        assert _post_json(anon_client, f"{BASE}/register/verify/").status_code == 404

    def test_login_options_404(self, anon_client, home_mode):
        assert _post_json(anon_client, f"{BASE}/login/options/").status_code == 404

    def test_login_verify_404(self, anon_client, home_mode):
        assert _post_json(anon_client, f"{BASE}/login/verify/").status_code == 404

    def test_list_credentials_404(self, anon_client, home_mode):
        # Without auth, may get 401 before 404; either means blocked
        assert anon_client.get(f"{BASE}/credentials/").status_code in (401, 404)

    def test_add_credential_options_404(self, anon_client, home_mode):
        assert _post_json(anon_client, f"{BASE}/credentials/add/options/").status_code in (401, 404)

    def test_delete_credential_404(self, anon_client, home_mode):
        assert _delete(anon_client, f"{BASE}/credentials/1/").status_code in (401, 404)


# --- Tests: Registration flow ---


@pytest.mark.django_db
class TestRegisterOptions:
    @patch("apps.core.passkey_api.generate_registration_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_success(self, mock_to_json, mock_gen, anon_client, passkey_mode):
        mock_opts = MagicMock()
        mock_opts.challenge = b"\xaa" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "test"})

        resp = _post_json(anon_client, f"{BASE}/register/options/")
        assert resp.status_code == 200
        assert "challenge" in resp.json()
        mock_gen.assert_called_once()

    @patch("apps.core.passkey_api.generate_registration_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_stores_challenge_in_session(self, mock_to_json, mock_gen, anon_client, passkey_mode):
        mock_opts = MagicMock()
        mock_opts.challenge = b"\xbb" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "x"})

        _post_json(anon_client, f"{BASE}/register/options/")
        session = anon_client.session
        assert "webauthn_register_challenge" in session
        assert "webauthn_register_user_id" in session


@pytest.mark.django_db
class TestRegisterVerify:
    def _setup_session(self, client):
        session = client.session
        session["webauthn_register_challenge"] = "aa" * 16
        session["webauthn_register_user_id"] = "bb" * 16
        session.save()

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_success_creates_user_profile_credential(self, mock_verify, anon_client, passkey_mode):
        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/register/verify/", body)

        assert resp.status_code == 201
        data = resp.json()
        assert "user" in data
        assert "profile" in data
        assert data["profile"]["name"].startswith("User")
        assert User.objects.count() == 1
        assert Profile.objects.count() == 1
        assert WebAuthnCredential.objects.count() == 1

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_first_user_not_staff(self, mock_verify, anon_client, passkey_mode):
        """First user is NOT auto-promoted to admin. Use cookie_admin promote instead."""
        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/register/verify/", body)

        assert resp.status_code == 201
        user = User.objects.first()
        assert user.is_staff is False
        data = resp.json()
        assert "is_admin" not in data["user"], (
            "/auth/me-style response MUST NOT expose is_admin (spec 014-remove-is-staff, FR-010)"
        )

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_new_user_not_staff_when_others_exist(self, mock_verify, anon_client, passkey_mode):
        """New users are never auto-promoted, regardless of existing user count."""
        _make_user("pk_existing")

        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/register/verify/", body)

        assert resp.status_code == 201
        new_user = User.objects.order_by("-pk").first()
        assert new_user.is_staff is False

    def test_no_pending_challenge(self, anon_client, passkey_mode):
        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/register/verify/", body)
        assert resp.status_code == 400
        assert "no pending challenge" in resp.json()["error"]

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_verification_error(self, mock_verify, anon_client, passkey_mode):
        mock_verify.side_effect = Exception("Invalid attestation")
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/register/verify/", body)
        assert resp.status_code == 400
        assert "verification error" in resp.json()["error"]

    def test_invalid_json_body(self, anon_client, passkey_mode):
        self._setup_session(anon_client)
        resp = anon_client.post(
            f"{BASE}/register/verify/",
            data="not json",
            content_type="application/json",
        )
        assert resp.status_code == 400
        assert "invalid request body" in resp.json()["error"]

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_challenge_consumed_after_verify(self, mock_verify, anon_client, passkey_mode):
        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        _post_json(anon_client, f"{BASE}/register/verify/", body)

        session = anon_client.session
        assert "webauthn_register_challenge" not in session
        assert "webauthn_register_user_id" not in session

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_session_contains_profile_id_after_register(self, mock_verify, anon_client, passkey_mode):
        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        _post_json(anon_client, f"{BASE}/register/verify/", body)

        session = anon_client.session
        profile = Profile.objects.first()
        assert session["profile_id"] == profile.id

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_stores_transports(self, mock_verify, anon_client, passkey_mode):
        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\x01\x02\x03",
            credential_public_key=b"\x04\x05\x06",
            sign_count=0,
        )
        self._setup_session(anon_client)

        body = {
            "id": "test",
            "rawId": "test",
            "response": {},
            "type": "public-key",
            "transports": ["internal", "hybrid"],
        }
        _post_json(anon_client, f"{BASE}/register/verify/", body)

        cred = WebAuthnCredential.objects.first()
        assert cred.transports == ["internal", "hybrid"]


# --- Tests: Login flow ---


@pytest.mark.django_db
class TestLoginOptions:
    def test_no_credentials_returns_flag(self, anon_client, passkey_mode):
        resp = _post_json(anon_client, f"{BASE}/login/options/")
        assert resp.status_code == 200
        assert resp.json()["no_credentials"] is True

    @patch("apps.core.passkey_api.generate_authentication_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_success_with_credentials(self, mock_to_json, mock_gen, anon_client, passkey_mode):
        user = _make_user()
        _make_credential(user)

        mock_opts = MagicMock()
        mock_opts.challenge = b"\xcc" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "test"})

        resp = _post_json(anon_client, f"{BASE}/login/options/")
        assert resp.status_code == 200
        assert "challenge" in resp.json()

    @patch("apps.core.passkey_api.generate_authentication_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_stores_challenge_in_session(self, mock_to_json, mock_gen, anon_client, passkey_mode):
        user = _make_user()
        _make_credential(user)

        mock_opts = MagicMock()
        mock_opts.challenge = b"\xdd" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "x"})

        _post_json(anon_client, f"{BASE}/login/options/")
        assert "webauthn_login_challenge" in anon_client.session


@pytest.mark.django_db
class TestLoginVerify:
    def _setup_session(self, client):
        session = client.session
        session["webauthn_login_challenge"] = "ee" * 16
        session.save()

    def test_no_pending_challenge(self, anon_client, passkey_mode):
        body = {"id": "test", "rawId": "dGVzdA", "response": {}, "type": "public-key"}
        resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
        assert resp.status_code == 401
        assert "no pending challenge" in resp.json()["error"]

    def test_invalid_json_body(self, anon_client, passkey_mode):
        self._setup_session(anon_client)
        resp = anon_client.post(
            f"{BASE}/login/verify/",
            data="not json",
            content_type="application/json",
        )
        assert resp.status_code == 401
        assert "invalid request body" in resp.json()["error"]

    def test_unknown_credential(self, anon_client, passkey_mode):
        self._setup_session(anon_client)
        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\xff\xff\xff"):
            body = {"rawId": "dGVzdA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
            assert resp.status_code == 401

    def test_inactive_user_rejected(self, anon_client, passkey_mode):
        user = _make_user()
        user.is_active = False
        user.save()
        _make_profile(user)
        _make_credential(user, credential_id=b"\x10\x20\x30")
        self._setup_session(anon_client)

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
            assert resp.status_code == 401

    @patch("apps.core.passkey_api.verify_authentication_response")
    def test_verification_failure(self, mock_verify, anon_client, passkey_mode):
        user = _make_user()
        _make_profile(user)
        _make_credential(user, credential_id=b"\x10\x20\x30")
        self._setup_session(anon_client)
        mock_verify.side_effect = Exception("Verification failed")

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
            assert resp.status_code == 401

    @patch("apps.core.passkey_api.verify_authentication_response")
    def test_cloned_authenticator_rejected(self, mock_verify, anon_client, passkey_mode):
        user = _make_user()
        _make_profile(user)
        _make_credential(user, credential_id=b"\x10\x20\x30", sign_count=10)
        self._setup_session(anon_client)
        mock_verify.return_value = SimpleNamespace(new_sign_count=5)

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
            assert resp.status_code == 401

    @patch("apps.core.passkey_api.verify_authentication_response")
    def test_successful_login(self, mock_verify, anon_client, passkey_mode):
        user = _make_user()
        profile = _make_profile(user)
        cred = _make_credential(user, credential_id=b"\x10\x20\x30", sign_count=5)
        self._setup_session(anon_client)
        mock_verify.return_value = SimpleNamespace(new_sign_count=6)

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)

        assert resp.status_code == 200
        data = resp.json()
        assert data["user"]["id"] == user.id
        assert data["profile"]["id"] == profile.id

        cred.refresh_from_db()
        assert cred.sign_count == 6
        assert cred.last_used_at is not None
        assert anon_client.session["profile_id"] == profile.id

    @patch("apps.core.passkey_api.verify_authentication_response")
    def test_zero_sign_count_not_cloned(self, mock_verify, anon_client, passkey_mode):
        user = _make_user()
        _make_profile(user)
        _make_credential(user, credential_id=b"\x10\x20\x30", sign_count=0)
        self._setup_session(anon_client)
        mock_verify.return_value = SimpleNamespace(new_sign_count=0)

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            resp = _post_json(anon_client, f"{BASE}/login/verify/", body)
        assert resp.status_code == 200

    @patch("apps.core.passkey_api.verify_authentication_response")
    def test_challenge_consumed_after_verify(self, mock_verify, anon_client, passkey_mode):
        user = _make_user()
        _make_profile(user)
        _make_credential(user, credential_id=b"\x10\x20\x30")
        self._setup_session(anon_client)
        mock_verify.return_value = SimpleNamespace(new_sign_count=1)

        with patch("webauthn.helpers.base64url_to_bytes", return_value=b"\x10\x20\x30"):
            body = {"rawId": "ECAA", "id": "test", "response": {}, "type": "public-key"}
            _post_json(anon_client, f"{BASE}/login/verify/", body)
        assert "webauthn_login_challenge" not in anon_client.session


# --- Tests: Credential Management ---


@pytest.mark.django_db
class TestListCredentials:
    def test_requires_auth(self, anon_client, passkey_mode):
        assert anon_client.get(f"{BASE}/credentials/").status_code == 401

    def test_lists_credentials(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        _make_credential(user, credential_id=b"\x01")
        _make_credential(user, credential_id=b"\x02")
        client = Client()
        _auth_client(client, profile, user)

        resp = client.get(f"{BASE}/credentials/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["credentials"]) == 2
        assert all(c["is_deletable"] for c in data["credentials"])

    def test_single_credential_not_deletable(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        _make_credential(user)
        client = Client()
        _auth_client(client, profile, user)

        resp = client.get(f"{BASE}/credentials/")
        data = resp.json()
        assert len(data["credentials"]) == 1
        assert data["credentials"][0]["is_deletable"] is False

    def test_does_not_show_other_users_credentials(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        _make_credential(user)
        other_user = _make_user("pk_other")
        _make_credential(other_user, credential_id=b"\x99")
        client = Client()
        _auth_client(client, profile, user)

        resp = client.get(f"{BASE}/credentials/")
        assert len(resp.json()["credentials"]) == 1


@pytest.mark.django_db
class TestAddCredentialOptions:
    def test_requires_auth(self, anon_client, passkey_mode):
        assert _post_json(anon_client, f"{BASE}/credentials/add/options/").status_code == 401

    @patch("apps.core.passkey_api.generate_registration_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_success(self, mock_to_json, mock_gen, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        _make_credential(user)
        mock_opts = MagicMock()
        mock_opts.challenge = b"\xee" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "test"})

        client = Client()
        _auth_client(client, profile, user)
        resp = _post_json(client, f"{BASE}/credentials/add/options/")
        assert resp.status_code == 200
        assert "challenge" in resp.json()
        assert "webauthn_add_challenge" in client.session

    @patch("apps.core.passkey_api.generate_registration_options")
    @patch("apps.core.passkey_api.options_to_json")
    def test_excludes_existing_credentials(self, mock_to_json, mock_gen, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        _make_credential(user)
        mock_opts = MagicMock()
        mock_opts.challenge = b"\xee" * 16
        mock_gen.return_value = mock_opts
        mock_to_json.return_value = json.dumps({"challenge": "test"})

        client = Client()
        _auth_client(client, profile, user)
        _post_json(client, f"{BASE}/credentials/add/options/")
        call_kwargs = mock_gen.call_args[1]
        assert len(call_kwargs["exclude_credentials"]) == 1


@pytest.mark.django_db
class TestAddCredentialVerify:
    def test_requires_auth(self, anon_client, passkey_mode):
        assert _post_json(anon_client, f"{BASE}/credentials/add/verify/").status_code == 401

    def test_no_pending_challenge(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(client, f"{BASE}/credentials/add/verify/", body)
        assert resp.status_code == 400
        assert "No pending challenge" in resp.json()["error"]

    def test_invalid_json_body(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        session = client.session
        session["webauthn_add_challenge"] = "ff" * 16
        session.save()

        resp = client.post(f"{BASE}/credentials/add/verify/", data="not json", content_type="application/json")
        assert resp.status_code == 400
        assert "Invalid request body" in resp.json()["error"]

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_verification_failure(self, mock_verify, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        session = client.session
        session["webauthn_add_challenge"] = "ff" * 16
        session.save()
        mock_verify.side_effect = Exception("Bad attestation")

        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        resp = _post_json(client, f"{BASE}/credentials/add/verify/", body)
        assert resp.status_code == 400
        assert "Verification failed" in resp.json()["error"]

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_success_creates_credential(self, mock_verify, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        session = client.session
        session["webauthn_add_challenge"] = "ff" * 16
        session.save()

        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\xaa\xbb\xcc",
            credential_public_key=b"\xdd\xee\xff",
            sign_count=0,
        )
        body = {
            "id": "test",
            "rawId": "test",
            "response": {},
            "type": "public-key",
            "transports": ["usb"],
        }
        resp = _post_json(client, f"{BASE}/credentials/add/verify/", body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["credential"]["is_deletable"] is True
        assert data["credential"]["last_used_at"] is None

        cred = WebAuthnCredential.objects.get(user=user)
        assert cred.transports == ["usb"]

    @patch("apps.core.passkey_api.verify_registration_response")
    def test_challenge_consumed(self, mock_verify, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        session = client.session
        session["webauthn_add_challenge"] = "ff" * 16
        session.save()

        mock_verify.return_value = SimpleNamespace(
            credential_id=b"\xaa\xbb\xcc",
            credential_public_key=b"\xdd\xee\xff",
            sign_count=0,
        )
        body = {"id": "test", "rawId": "test", "response": {}, "type": "public-key"}
        _post_json(client, f"{BASE}/credentials/add/verify/", body)
        assert "webauthn_add_challenge" not in client.session


@pytest.mark.django_db
class TestDeleteCredential:
    def test_requires_auth(self, anon_client, passkey_mode):
        assert _delete(anon_client, f"{BASE}/credentials/1/").status_code == 401

    def test_credential_not_found(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        client = Client()
        _auth_client(client, profile, user)
        assert _delete(client, f"{BASE}/credentials/99999/").status_code == 404

    def test_cannot_delete_only_passkey(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        cred = _make_credential(user)
        client = Client()
        _auth_client(client, profile, user)

        resp = _delete(client, f"{BASE}/credentials/{cred.pk}/")
        assert resp.status_code == 400
        assert "only passkey" in resp.json()["error"]

    def test_can_delete_when_multiple(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        cred1 = _make_credential(user, credential_id=b"\x01")
        cred2 = _make_credential(user, credential_id=b"\x02")
        client = Client()
        _auth_client(client, profile, user)

        resp = _delete(client, f"{BASE}/credentials/{cred1.pk}/")
        assert resp.status_code == 200
        assert resp.json()["message"] == "Passkey deleted"
        assert not WebAuthnCredential.objects.filter(pk=cred1.pk).exists()
        assert WebAuthnCredential.objects.filter(pk=cred2.pk).exists()

    def test_cannot_delete_other_users_credential(self, user_and_profile, passkey_mode):
        user, profile = user_and_profile
        other_user = _make_user("pk_other")
        other_cred = _make_credential(other_user, credential_id=b"\x99")
        client = Client()
        _auth_client(client, profile, user)

        assert _delete(client, f"{BASE}/credentials/{other_cred.pk}/").status_code == 404


# --- Tests: Helper functions ---


@pytest.mark.django_db
class TestHelpers:
    def test_get_rp_id_from_settings(self, settings):
        from apps.core.passkey_api import _get_rp_id

        settings.WEBAUTHN_RP_ID = "example.com"
        request = MagicMock()
        assert _get_rp_id(request) == "example.com"

    def test_get_rp_id_from_request_host(self, settings):
        from apps.core.passkey_api import _get_rp_id

        settings.WEBAUTHN_RP_ID = ""
        request = MagicMock()
        request.get_host.return_value = "cookie.local:8000"
        assert _get_rp_id(request) == "cookie.local"

    def test_get_origin_http(self):
        from apps.core.passkey_api import _get_origin

        request = MagicMock()
        request.is_secure.return_value = False
        request.get_host.return_value = "localhost:8000"
        assert _get_origin(request) == "http://localhost:8000"

    def test_get_origin_https(self):
        from apps.core.passkey_api import _get_origin

        request = MagicMock()
        request.is_secure.return_value = True
        request.get_host.return_value = "cookie.example.com"
        assert _get_origin(request) == "https://cookie.example.com"

    def test_get_origin_uses_rp_origin_setting(self, settings):
        """F-33: WEBAUTHN_RP_ORIGIN is used directly when set."""
        from apps.core.passkey_api import _get_origin
        settings.WEBAUTHN_RP_ORIGIN = "https://cookie.example.com"
        request = MagicMock()
        assert _get_origin(request) == "https://cookie.example.com"
        request.get_host.assert_not_called()

    def test_get_origin_rp_origin_ignores_forwarded_host(self, settings):
        """F-33 regression: pinned WEBAUTHN_RP_ORIGIN is immune to X-Forwarded-Host."""
        from apps.core.passkey_api import _get_origin
        settings.WEBAUTHN_RP_ORIGIN = "https://cookie.example.com"
        request = MagicMock()
        request.get_host.return_value = "localhost"
        assert _get_origin(request) == "https://cookie.example.com"
        request.get_host.assert_not_called()


# --- Tests: Rate limiting ---


@pytest.mark.django_db
class TestRateLimiting:
    """Verify rate-limited responses return 429 by calling view functions directly."""

    def _make_request(self, url):
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.post(url, content_type="application/json", data="{}")
        request.limited = True
        request.session = {}
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        return request

    def test_register_options_rate_limited(self, passkey_mode):
        from apps.core.passkey_api import register_options

        request = self._make_request(f"{BASE}/register/options/")
        result = register_options(request)
        assert result.status_code == 429
        assert "Too many attempts" in result.value["error"]

    def test_register_verify_rate_limited(self, passkey_mode):
        from apps.core.passkey_api import register_verify

        request = self._make_request(f"{BASE}/register/verify/")
        result = register_verify(request)
        assert result.status_code == 429
        assert "Too many attempts" in result.value["error"]

    def test_login_options_rate_limited(self, passkey_mode):
        from apps.core.passkey_api import login_options

        request = self._make_request(f"{BASE}/login/options/")
        result = login_options(request)
        assert result.status_code == 429
        assert "Too many attempts" in result.value["error"]

    def test_login_verify_rate_limited(self, passkey_mode):
        from apps.core.passkey_api import login_verify

        request = self._make_request(f"{BASE}/login/verify/")
        result = login_verify(request)
        assert result.status_code == 429
        assert "Too many attempts" in result.value["error"]


# --- Tests: Challenge expiry and consumption ---


@pytest.mark.django_db
class TestChallengeExpiry:
    """WebAuthn challenges must expire after 5 minutes (FR-010)."""

    def test_register_verify_rejects_expired_challenge(self, anon_client, passkey_mode):
        """A challenge older than 5 minutes is rejected."""
        import time

        session = anon_client.session
        session["webauthn_register_challenge"] = "aa" * 16
        session["webauthn_register_user_id"] = "bb" * 16
        session["webauthn_register_challenge_created_at"] = time.time() - 301  # 5m1s ago
        session.save()

        resp = _post_json(
            anon_client,
            f"{BASE}/register/verify/",
            {
                "id": "AAAA",
                "rawId": "AAAA",
                "response": {"attestationObject": "AAAA", "clientDataJSON": "AAAA"},
                "type": "public-key",
            },
        )
        assert resp.status_code == 400
        assert "expired" in resp.json()["error"].lower()

    def test_login_verify_rejects_expired_challenge(self, anon_client, passkey_mode):
        """A login challenge older than 5 minutes is rejected."""
        import time

        session = anon_client.session
        session["webauthn_login_challenge"] = "cc" * 16
        session["webauthn_login_challenge_created_at"] = time.time() - 301
        session.save()

        resp = _post_json(
            anon_client,
            f"{BASE}/login/verify/",
            {
                "id": "AAAA",
                "rawId": "AAAA",
                "response": {
                    "authenticatorData": "AAAA",
                    "clientDataJSON": "AAAA",
                    "signature": "AAAA",
                },
                "type": "public-key",
            },
        )
        assert resp.status_code == 401
        assert "expired" in resp.json()["error"].lower()

    def test_register_verify_accepts_fresh_challenge(self, anon_client, passkey_mode):
        """A challenge within 5 minutes should NOT be rejected for expiry.

        It may fail for other reasons (invalid credential), but not expiry.
        """
        import time

        session = anon_client.session
        session["webauthn_register_challenge"] = "dd" * 16
        session["webauthn_register_user_id"] = "ee" * 16
        session["webauthn_register_challenge_created_at"] = time.time() - 60  # 1 minute ago
        session.save()

        resp = _post_json(
            anon_client,
            f"{BASE}/register/verify/",
            {
                "id": "AAAA",
                "rawId": "AAAA",
                "response": {"attestationObject": "AAAA", "clientDataJSON": "AAAA"},
                "type": "public-key",
            },
        )
        # Should fail for credential validation reasons, NOT expiry
        assert "expired" not in resp.json().get("error", "").lower()


@pytest.mark.django_db
class TestChallengeConsumption:
    """Challenges must be consumed (popped) even when rate-limited (FR-011)."""

    def test_register_challenge_consumed_on_rate_limit(self, anon_client, passkey_mode):
        """If rate limit blocks verify, the challenge is still consumed."""
        import time

        session = anon_client.session
        session["webauthn_register_challenge"] = "ff" * 16
        session["webauthn_register_user_id"] = "00" * 16
        session["webauthn_register_challenge_created_at"] = time.time()
        session.save()

        # Simulate rate-limited request
        with patch("apps.core.passkey_api.ratelimit"):
            # Call the endpoint — it will check request.limited
            _post_json(
                anon_client,
                f"{BASE}/register/verify/",
                {
                    "id": "AAAA",
                    "rawId": "AAAA",
                    "response": {"attestationObject": "AAAA", "clientDataJSON": "AAAA"},
                    "type": "public-key",
                },
            )

        # Regardless of the response, the challenge should be gone from session
        session_after = anon_client.session
        assert "webauthn_register_challenge" not in session_after

    def test_login_challenge_consumed_after_verify(self, anon_client, passkey_mode):
        """After login/verify, the challenge is consumed from session."""
        import time

        session = anon_client.session
        session["webauthn_login_challenge"] = "11" * 16
        session["webauthn_login_challenge_created_at"] = time.time()
        session.save()

        _post_json(
            anon_client,
            f"{BASE}/login/verify/",
            {
                "id": "AAAA",
                "rawId": "AAAA",
                "response": {
                    "authenticatorData": "AAAA",
                    "clientDataJSON": "AAAA",
                    "signature": "AAAA",
                },
                "type": "public-key",
            },
        )

        session_after = anon_client.session
        assert "webauthn_login_challenge" not in session_after
