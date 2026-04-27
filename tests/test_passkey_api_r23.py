"""R23 regression tests — challenge TTL key isolation and non-sequential profile names.

Split from test_passkey_api.py to keep that file under its grandfathered 920-line ceiling.
"""
import re
import time
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.core.models import WebAuthnCredential
from apps.core.passkey_api import _create_passkey_user_and_profile
from apps.profiles.models import Profile

BASE = "/api/auth/passkey"


@pytest.fixture
def anon_client():
    return Client()


@pytest.fixture
def passkey_mode(settings):
    settings.AUTH_MODE = "passkey"


# --- Challenge created_at key isolation (R23 F-34) ---


@pytest.mark.django_db
class TestChallengeCreatedAtKeyIsolation:
    """Per-type webauthn_*_challenge_created_at keys must not cross-contaminate (R23 F-34).

    Previously all three options endpoints wrote to the shared key
    webauthn_challenge_created_at. Calling register_options after login_options
    overwrote the timestamp, resetting the TTL clock for the login challenge and
    allowing an indefinite window extension. Fix: each challenge type uses its own key.
    """

    def test_register_options_does_not_overwrite_login_created_at(
        self, anon_client, passkey_mode
    ):
        """register_options must write webauthn_register_challenge_created_at,
        leaving webauthn_login_challenge_created_at untouched."""
        session = anon_client.session
        sentinel = time.time() - 100
        session["webauthn_login_challenge"] = "aa" * 16
        session["webauthn_login_challenge_created_at"] = sentinel
        session.save()

        anon_client.post(f"{BASE}/register/options/", content_type="application/json")

        session_after = anon_client.session
        assert session_after.get("webauthn_login_challenge_created_at") == sentinel
        reg_ts = session_after.get("webauthn_register_challenge_created_at")
        assert reg_ts is not None
        assert time.time() - reg_ts < 5

    def test_login_options_does_not_overwrite_register_created_at(
        self, anon_client, passkey_mode
    ):
        """login_options must write webauthn_login_challenge_created_at,
        leaving webauthn_register_challenge_created_at untouched."""
        user = User.objects.create_user(username="pk_iso_test", password=None)
        user.set_unusable_password()
        user.save()
        WebAuthnCredential.objects.create(
            user=user,
            credential_id=b"iso_test_cred_id_001",
            public_key=b"fake_pubkey",
            sign_count=0,
        )

        session = anon_client.session
        sentinel = time.time() - 200
        session["webauthn_register_challenge"] = "bb" * 16
        session["webauthn_register_challenge_created_at"] = sentinel
        session.save()

        anon_client.post(f"{BASE}/login/options/", content_type="application/json")

        session_after = anon_client.session
        assert session_after.get("webauthn_register_challenge_created_at") == sentinel
        login_ts = session_after.get("webauthn_login_challenge_created_at")
        assert login_ts is not None
        assert time.time() - login_ts < 5

    def test_add_credential_options_does_not_overwrite_login_created_at(
        self, passkey_mode
    ):
        """add_credential_options must write webauthn_add_challenge_created_at,
        leaving webauthn_login_challenge_created_at untouched."""
        user = User.objects.create_user(username="pk_add_iso", password=None)
        user.set_unusable_password()
        user.save()
        profile = Profile.objects.create(user=user, name="Test User")
        WebAuthnCredential.objects.create(
            user=user,
            credential_id=b"add_iso_cred_id_001",
            public_key=b"fake_pubkey",
            sign_count=0,
        )

        client = Client()
        client.force_login(user)
        session = client.session
        session["profile_id"] = profile.id  # required by Cookie's SessionAuth
        sentinel = time.time() - 50
        session["webauthn_login_challenge"] = "cc" * 16
        session["webauthn_login_challenge_created_at"] = sentinel
        session.save()

        client.post(
            f"{BASE}/credentials/add/options/",
            content_type="application/json",
        )

        session_after = client.session
        assert session_after.get("webauthn_login_challenge_created_at") == sentinel
        add_ts = session_after.get("webauthn_add_challenge_created_at")
        assert add_ts is not None
        assert time.time() - add_ts < 5


# --- Profile name is non-sequential (R23 finding) ---


@pytest.mark.django_db
class TestProfileNameNonSequential:
    """register_verify must not leak user count via sequential 'User N' profile names (R23)."""

    def test_profile_name_does_not_reveal_user_count(self, passkey_mode):
        """Profile name must NOT match 'User <integer>'."""
        mock_verification = SimpleNamespace(
            credential_id=b"test_cred_id_profile_name",
            credential_public_key=b"fake_pubkey",
            sign_count=0,
        )
        _, profile = _create_passkey_user_and_profile(mock_verification)
        assert not re.match(r"^User \d+$", profile.name), (
            f"Profile name '{profile.name}' is a sequential 'User N' — leaks user count"
        )

    def test_profile_name_has_random_suffix(self, passkey_mode):
        """Profile names from two back-to-back registrations must differ."""
        v1 = SimpleNamespace(
            credential_id=b"cred_profile_name_1",
            credential_public_key=b"pk1",
            sign_count=0,
        )
        v2 = SimpleNamespace(
            credential_id=b"cred_profile_name_2",
            credential_public_key=b"pk2",
            sign_count=0,
        )
        _, p1 = _create_passkey_user_and_profile(v1)
        _, p2 = _create_passkey_user_and_profile(v2)
        assert p1.name != p2.name, "Two consecutive registrations produced identical profile names"
