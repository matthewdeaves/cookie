"""Authentication API endpoints — public and passkey mode shared endpoints."""

import logging
import re

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import SessionAuth
from apps.core.email_service import send_verification_email, validate_verification_token
from apps.profiles.models import Profile

security_logger = logging.getLogger("security")

router = Router(tags=["auth"])

USERNAME_PATTERN = re.compile(r"^[a-zA-Z0-9_]+$")


def _require_public_mode(request):
    """Raise 404 if not in public mode."""
    if settings.AUTH_MODE != "public":
        from django.http import Http404

        raise Http404


def _require_public_or_passkey_mode(request):
    """Raise 404 if not in public or passkey mode."""
    if settings.AUTH_MODE not in ("public", "passkey"):
        from django.http import Http404

        raise Http404


# --- Schemas ---


class RegisterIn(Schema):
    username: str
    password: str
    password_confirm: str
    email: str
    privacy_accepted: bool


class LoginIn(Schema):
    username: str
    password: str


class ChangePasswordIn(Schema):
    current_password: str
    new_password: str
    new_password_confirm: str


class UserOut(Schema):
    id: int
    username: str
    is_admin: bool


class ProfileOut(Schema):
    id: int
    name: str
    avatar_color: str
    theme: str
    unit_preference: str


class AuthResponse(Schema):
    user: UserOut
    profile: ProfileOut


# --- Helpers ---


def _user_profile_response(user, profile):
    return {
        "user": {"id": user.id, "username": user.username, "is_admin": user.is_staff},
        "profile": {
            "id": profile.id,
            "name": profile.name,
            "avatar_color": profile.avatar_color,
            "theme": profile.theme,
            "unit_preference": profile.unit_preference,
        },
    }


from apps.core.auth_helpers import passkey_user_profile_response as _passkey_user_profile_response


def _validate_username(username):
    errors = []
    if len(username) < 3 or len(username) > 30:
        errors.append("Username must be 3-30 characters")
    if not USERNAME_PATTERN.match(username):
        errors.append("Username can only contain letters, numbers, and underscores")
    return errors


def _validate_registration(data):
    errors = {}

    username_errors = _validate_username(data.username)
    if username_errors:
        errors["username"] = username_errors

    if data.password != data.password_confirm:
        errors["password_confirm"] = ["Passwords do not match"]

    try:
        validate_password(data.password)
    except DjangoValidationError as e:
        errors["password"] = list(e.messages)

    try:
        validate_email(data.email)
    except DjangoValidationError:
        errors["email"] = ["Invalid email format"]

    if not data.privacy_accepted:
        errors["privacy_accepted"] = ["You must accept the privacy policy"]

    return errors


@transaction.atomic
def _create_user_and_profile(data):
    """Create user + profile atomically. Handles stale replacement and auto-admin."""
    # Check username uniqueness (case-insensitive) inside transaction
    existing = User.objects.select_for_update().filter(username__iexact=data.username).first()
    if existing:
        two_hours_ago = timezone.now() - timezone.timedelta(hours=2)
        if not existing.is_active and existing.date_joined < two_hours_ago:
            existing.delete()
        else:
            return None, {"username": ["Username already taken"]}

    # Determine if first user (auto-admin) — inside transaction for atomicity
    is_first_user = not User.objects.filter(is_active=True).exists()

    user = User.objects.create_user(
        username=data.username,
        password=data.password,
        email="",  # NEVER store email
        is_active=False,
        is_staff=is_first_user,
    )

    Profile.objects.create(
        user=user,
        name=data.username,
        avatar_color=Profile.next_avatar_color(),
    )

    return user, None


# --- Endpoints ---


@router.post("/register/", response={201: dict, 400: dict, 429: dict})
@ratelimit(key="ip", rate="5/h", method="POST", block=False)
def register(request, data: RegisterIn):
    _require_public_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /auth/register/ from %s", request.META.get("REMOTE_ADDR"))
        return 429, {"error": "Too many registration attempts. Please try again later."}

    errors = _validate_registration(data)
    if errors:
        return 400, {"errors": errors}

    user, db_errors = _create_user_and_profile(data)
    if db_errors:
        return 400, {"errors": db_errors}

    # Send verification email (transient — email only in memory)
    try:
        send_verification_email(user.id, data.email)
    except Exception:
        security_logger.warning("Failed to send verification email for user_id=%s", user.id)
        # Delete the user so they can retry immediately
        user.delete()
        return 400, {"errors": {"email": ["Failed to send verification email. Please try again."]}}

    security_logger.info("Registration: user=%s from %s", data.username, request.META.get("REMOTE_ADDR"))

    return 201, {
        "message": "Account created. Check your email to verify your account. The verification link expires in 2 hours."
    }


@router.get("/verify-email/")
def verify_email(request):
    _require_public_mode(request)
    token = request.GET.get("token", "")
    user_id = validate_verification_token(token)

    if user_id is None:
        return TemplateResponse(request, "core/verification_failed.html", status=400)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return TemplateResponse(request, "core/verification_failed.html", status=400)

    # Idempotent — already active means token was used
    if not user.is_active:
        user.is_active = True
        user.save(update_fields=["is_active"])
        security_logger.info("Email verification success: user=%s", user.username)

    # Redirect based on device
    if getattr(request, "is_legacy_device", False):
        return redirect("/legacy/?verified=true")
    return redirect("/?verified=true")


@router.post("/login/", response={200: AuthResponse, 401: dict, 403: dict, 429: dict})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def login_view(request, data: LoginIn):
    _require_public_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning("Rate limit hit: /auth/login/ from %s", request.META.get("REMOTE_ADDR"))
        return 429, {"error": "Too many login attempts. Please try again later."}

    user = authenticate(request, username=data.username, password=data.password)

    if user is None:
        # Check if this is an inactive user (Django's authenticate returns None for inactive)
        try:
            maybe_user = User.objects.get(username__iexact=data.username)
            if not maybe_user.is_active and maybe_user.check_password(data.password):
                return 403, {"error": "Account not verified. Check your email for the verification link."}
        except User.DoesNotExist:
            pass
        security_logger.warning("Login failure from %s", request.META.get("REMOTE_ADDR"))
        return 401, {"error": "Invalid username or password"}

    login(request, user)
    request.session["profile_id"] = user.profile.id

    security_logger.info("Login success: user=%s from %s", user.username, request.META.get("REMOTE_ADDR"))

    return 200, _user_profile_response(user, user.profile)


@router.post("/logout/", response={200: dict}, auth=SessionAuth())
def logout_view(request):
    _require_public_or_passkey_mode(request)
    username = getattr(request, "user", None)
    username = username.username if username and hasattr(username, "username") else "unknown"
    logout(request)
    security_logger.info("Logout: user=%s", username)
    return {"message": "Logged out successfully"}


@router.get("/me/", response={200: dict, 401: dict}, auth=SessionAuth())
def get_me(request):
    _require_public_or_passkey_mode(request)
    user = request.user
    if not user or not getattr(user, "is_authenticated", False):
        return 401, {"error": "Authentication required"}

    try:
        profile = user.profile
    except Profile.DoesNotExist:
        return 401, {"error": "Authentication required"}

    if settings.AUTH_MODE == "passkey":
        return 200, _passkey_user_profile_response(user, profile)
    return 200, _user_profile_response(user, profile)


@router.post("/change-password/", response={200: dict, 400: dict, 429: dict}, auth=SessionAuth())
@ratelimit(key="user", rate="5/h", method="POST", block=False)
def change_password(request, data: ChangePasswordIn):
    _require_public_mode(request)
    if getattr(request, "limited", False):
        return 429, {"error": "Too many password change attempts. Please try again later."}

    user = request.user

    if not user.check_password(data.current_password):
        return 400, {"errors": {"current_password": ["Incorrect password"]}}

    if data.new_password != data.new_password_confirm:
        return 400, {"errors": {"new_password_confirm": ["Passwords do not match"]}}

    try:
        validate_password(data.new_password, user=user)
    except DjangoValidationError as e:
        return 400, {"errors": {"new_password": list(e.messages)}}

    user.set_password(data.new_password)
    user.save(update_fields=["password"])

    # Re-authenticate to keep session valid
    login(request, user)

    security_logger.info("Password changed: user=%s", user.username)
    return {"message": "Password changed successfully"}
