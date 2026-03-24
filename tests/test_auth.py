"""Tests for authentication endpoints (public mode)."""

import json
from unittest.mock import patch

import pytest
from django.contrib.auth.models import User
from django.test import Client

from apps.core.email_service import generate_verification_token, validate_verification_token
from apps.profiles.models import Profile


@pytest.fixture
def public_client():
    return Client()


@pytest.fixture(autouse=False)
def public_mode(settings):
    """Switch to public mode."""
    settings.AUTH_MODE = "public"


def _register(client, username="testuser", password="StrongPass123!", email="test@example.com"):  # noqa: S107
    return client.post(
        "/api/auth/register/",
        data=json.dumps({
            "username": username,
            "password": password,
            "password_confirm": password,
            "email": email,
            "privacy_accepted": True,
        }),
        content_type="application/json",
    )


def _login(client, username="testuser", password="StrongPass123!"):  # noqa: S107
    return client.post(
        "/api/auth/login/",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )


def _create_active_user(username="testuser", password="StrongPass123!", is_staff=False):  # noqa: S107
    user = User.objects.create_user(username=username, password=password, email="", is_active=True, is_staff=is_staff)
    Profile.objects.create(user=user, name=username, avatar_color="#d97850")
    return user


@pytest.mark.django_db
class TestTokens:
    """T019: Token generation and validation."""

    def test_valid_token(self):
        user = User.objects.create_user(username="tok", password="pass12345678", email="")
        token = generate_verification_token(user.id)
        assert validate_verification_token(token) == user.id

    def test_tampered_token(self):
        user = User.objects.create_user(username="tok2", password="pass12345678", email="")
        token = generate_verification_token(user.id) + "tampered"
        assert validate_verification_token(token) is None

    @patch("apps.core.email_service.VERIFICATION_MAX_AGE", 0)
    def test_expired_token(self):
        import time

        user = User.objects.create_user(username="tok3", password="pass12345678", email="")
        token = generate_verification_token(user.id)
        time.sleep(1)
        assert validate_verification_token(token) is None


@pytest.mark.django_db
class TestRegistration:
    """T037-T050: Registration tests."""

    @patch("apps.core.auth_api.send_verification_email")
    def test_successful_registration(self, mock_email, public_client, public_mode):
        """T037: Registration creates inactive user with empty email."""
        response = _register(public_client)
        assert response.status_code == 201
        user = User.objects.get(username="testuser")
        assert not user.is_active
        assert user.email == ""

    @patch("apps.core.auth_api.send_verification_email")
    def test_email_not_stored(self, mock_email, public_client, public_mode):
        """T038: After registration, User.email == ''."""
        _register(public_client, email="secret@example.com")
        user = User.objects.get(username="testuser")
        assert user.email == ""

    @patch("apps.core.auth_api.send_verification_email")
    def test_taken_username(self, mock_email, public_client, public_mode):
        """T039: Registration with taken username returns 400."""
        User.objects.create_user(username="testuser", password="pass12345678", email="", is_active=True)
        response = _register(public_client)
        assert response.status_code == 400

    def test_weak_password(self, public_client, public_mode):
        """T040: Weak password returns 400."""
        response = _register(public_client, password="123")
        assert response.status_code == 400

    def test_mismatched_passwords(self, public_client, public_mode):
        """T041: Mismatched passwords returns 400."""
        response = public_client.post(
            "/api/auth/register/",
            data=json.dumps({
                "username": "testuser", "password": "StrongPass123!",
                "password_confirm": "DifferentPass!", "email": "t@e.com", "privacy_accepted": True,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_privacy_not_accepted(self, public_client, public_mode):
        """T042: privacy_accepted=false returns 400."""
        response = public_client.post(
            "/api/auth/register/",
            data=json.dumps({
                "username": "testuser", "password": "StrongPass123!",
                "password_confirm": "StrongPass123!", "email": "t@e.com", "privacy_accepted": False,
            }),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_invalid_email(self, public_client, public_mode):
        """T043: Invalid email returns 400."""
        response = _register(public_client, email="not-an-email")
        assert response.status_code == 400

    @patch("apps.core.auth_api.send_verification_email")
    def test_first_user_is_admin(self, mock_email, public_client, public_mode):
        """T048: First registration auto-promotes to admin."""
        _register(public_client, username="firstuser")
        user = User.objects.get(username="firstuser")
        assert user.is_staff is True

    @patch("apps.core.auth_api.send_verification_email")
    def test_second_user_not_admin(self, mock_email, public_client, public_mode):
        """T049: Second registration NOT auto-admin."""
        User.objects.create_user(username="admin", password="pass12345678", email="", is_active=True, is_staff=True)
        _register(public_client, username="second")
        assert User.objects.get(username="second").is_staff is False


@pytest.mark.django_db
class TestVerification:
    """T044-T047: Email verification tests."""

    def test_valid_token_activates(self, public_client, public_mode):
        """T044: Valid token activates user."""
        user = User.objects.create_user(username="v", password="pass12345678", email="", is_active=False)
        Profile.objects.create(user=user, name="v", avatar_color="#d97850")
        token = generate_verification_token(user.id)
        response = public_client.get(f"/api/auth/verify-email/?token={token}")
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.is_active is True

    def test_already_active_redirects(self, public_client, public_mode):
        """T047: Already-used token redirects."""
        user = User.objects.create_user(username="v2", password="pass12345678", email="", is_active=True)
        Profile.objects.create(user=user, name="v2", avatar_color="#d97850")
        token = generate_verification_token(user.id)
        response = public_client.get(f"/api/auth/verify-email/?token={token}")
        assert response.status_code == 302

    def test_tampered_token_fails(self, public_client, public_mode):
        """T046: Tampered token returns error."""
        response = public_client.get("/api/auth/verify-email/?token=bad-token")
        assert response.status_code == 400


@pytest.mark.django_db
class TestLogin:
    """T063-T070: Login tests."""

    def test_correct_credentials(self, public_client, public_mode):
        _create_active_user()
        response = _login(public_client)
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "testuser"

    def test_wrong_password(self, public_client, public_mode):
        _create_active_user()
        response = _login(public_client, password="wrongpass123")
        assert response.status_code == 401

    def test_nonexistent_username(self, public_client, public_mode):
        response = _login(public_client, username="nonexistent")
        assert response.status_code == 401

    def test_unverified_account(self, public_client, public_mode):
        User.objects.create_user(username="unverified", password="StrongPass123!", email="", is_active=False)
        response = _login(public_client, username="unverified")
        assert response.status_code == 403

    def test_logout_clears_session(self, public_client, public_mode):
        _create_active_user()
        _login(public_client)
        response = public_client.post("/api/auth/logout/")
        assert response.status_code == 200
        response = public_client.get("/api/auth/me/")
        assert response.status_code == 401

    def test_me_returns_user(self, public_client, public_mode):
        _create_active_user()
        _login(public_client)
        response = public_client.get("/api/auth/me/")
        assert response.status_code == 200
        assert response.json()["user"]["username"] == "testuser"

    def test_me_unauthenticated(self, public_client, public_mode):
        response = public_client.get("/api/auth/me/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestChangePassword:

    def test_change_password_success(self, public_client, public_mode):
        _create_active_user()
        _login(public_client)
        response = public_client.post(
            "/api/auth/change-password/",
            data=json.dumps({"current_password": "StrongPass123!", "new_password": "NewStrong456!", "new_password_confirm": "NewStrong456!"}),
            content_type="application/json",
        )
        assert response.status_code == 200

    def test_wrong_current_password(self, public_client, public_mode):
        _create_active_user()
        _login(public_client)
        response = public_client.post(
            "/api/auth/change-password/",
            data=json.dumps({"current_password": "Wrong!", "new_password": "NewStrong456!", "new_password_confirm": "NewStrong456!"}),
            content_type="application/json",
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestAccountDeletion:

    def test_deletion_removes_all_data(self, public_client, public_mode):
        user = _create_active_user()
        pid = user.profile.id
        _login(public_client)
        response = public_client.delete(f"/api/profiles/{pid}/")
        assert response.status_code == 204
        assert not User.objects.filter(username="testuser").exists()
        assert not Profile.objects.filter(id=pid).exists()

    def test_session_invalidated(self, public_client, public_mode):
        user = _create_active_user()
        _login(public_client)
        public_client.delete(f"/api/profiles/{user.profile.id}/")
        response = public_client.get("/api/auth/me/")
        assert response.status_code == 401


@pytest.mark.django_db
class TestPrivacyPolicy:

    def test_accessible_without_auth(self, client):
        response = client.get("/privacy/")
        assert response.status_code == 200

    def test_contains_required_elements(self, client):
        response = client.get("/privacy/")
        content = response.content.decode()
        assert "what data we collect" in content.lower()
        assert "ICO" in content or "Information Commissioner" in content
