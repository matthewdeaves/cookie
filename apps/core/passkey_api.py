"""Passkey (WebAuthn) authentication API endpoints — only active in passkey mode."""

import json
import logging
import secrets
import string
import time
import uuid

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from ninja import Router, Status
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from apps.core.auth import SessionAuth
from apps.core.auth_helpers import passkey_user_profile_response, require_passkey_mode
from apps.core.models import WebAuthnCredential
from apps.profiles.models import Profile

security_logger = logging.getLogger("security")

router = Router(tags=["passkey"])

_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


def _get_rp_id(request):
    """Get the Relying Party ID from settings or request hostname."""
    if settings.WEBAUTHN_RP_ID:
        return settings.WEBAUTHN_RP_ID
    return request.get_host().split(":")[0]


def _get_origin(request):
    """Get the expected origin for WebAuthn verification.

    When WEBAUTHN_RP_ORIGIN is set (production), returns that pinned value.
    This decouples origin binding from the request Host header, preventing
    X-Forwarded-Host injection from influencing the expected origin (F-33).

    Falls back to deriving from request host when WEBAUTHN_RP_ORIGIN is not
    set (development use without a fixed domain).
    """
    if settings.WEBAUTHN_RP_ORIGIN:
        return settings.WEBAUTHN_RP_ORIGIN
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{request.get_host()}"


# --- Registration ---


@router.post("/register/options/", response={200: dict, 400: dict, 429: dict})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def register_options(request):
    """Generate WebAuthn registration challenge."""
    require_passkey_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: passkey register/options/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return Status(429, {"error": "Too many attempts. Please try again later."})

    user_id = uuid.uuid4().bytes
    options = generate_registration_options(
        rp_id=_get_rp_id(request),
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_name="New User",
        user_id=user_id,
        user_display_name="New User",
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
    )

    # Store challenge, user_id, and creation timestamp in session
    request.session["webauthn_register_challenge"] = options.challenge.hex()
    request.session["webauthn_register_user_id"] = user_id.hex()
    request.session["webauthn_register_challenge_created_at"] = time.time()

    return Status(200, json.loads(options_to_json(options)))


@router.post("/register/verify/", response={201: dict, 400: dict, 429: dict})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def register_verify(request):
    """Verify registration response and create account."""
    require_passkey_mode(request)

    # Consume challenge BEFORE rate limit check to prevent replay (FR-011)
    challenge_hex = request.session.pop("webauthn_register_challenge", None)
    user_id_hex = request.session.pop("webauthn_register_user_id", None)
    created_at = request.session.pop("webauthn_register_challenge_created_at", None)

    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: passkey register/verify/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return Status(429, {"error": "Too many attempts. Please try again later."})

    if not challenge_hex or not user_id_hex:
        return Status(400, {"error": "Registration failed: no pending challenge"})

    # Reject expired challenges (FR-010: 5-minute window)
    if created_at and (time.time() - created_at) > 300:
        return Status(400, {"error": "Registration failed: challenge expired"})

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return Status(400, {"error": "Registration failed: invalid request body"})

    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=_get_rp_id(request),
            expected_origin=_get_origin(request),
            require_user_verification=True,
        )
    except Exception as e:
        security_logger.warning(
            "Passkey registration verification failed from %s: %s",
            request.META.get("REMOTE_ADDR"),
            str(e),
        )
        return Status(400, {"error": "Registration failed: verification error"})

    user, profile = _create_passkey_user_and_profile(verification, body.get("transports"))
    login(request, user, backend=_AUTH_BACKEND)
    request.session["profile_id"] = profile.id

    security_logger.info(
        "Passkey registration: user_id=%s from %s",
        user.pk,
        request.META.get("REMOTE_ADDR"),
    )

    return Status(201, passkey_user_profile_response(user, profile))


@transaction.atomic
def _create_passkey_user_and_profile(verification, transports=None):
    """Create User, Profile, and WebAuthnCredential atomically."""
    username = f"pk_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(
        username=username,
        password=None,
        email="",
        is_active=True,
        is_staff=False,
    )
    user.set_unusable_password()
    user.save(update_fields=["password"])

    # First char is forced to a letter so the suffix can never collapse to all
    # digits. uuid.uuid4().hex[:6] is hex (0-9a-f) — ~5.6% of draws are all
    # digits, which then matches `^User \d+$` and trips R23's "user count
    # leak" guard. The remaining 5 hex chars carry the entropy.
    suffix = secrets.choice(string.ascii_lowercase) + uuid.uuid4().hex[:5]
    profile = Profile.objects.create(
        user=user,
        name=f"User {suffix}",
        avatar_color=Profile.next_avatar_color(),
    )

    WebAuthnCredential.objects.create(
        user=user,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=transports,
    )

    return user, profile


# --- Authentication ---


@router.post("/login/options/", response={200: dict, 429: dict})
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
def login_options(request):
    """Generate WebAuthn authentication challenge."""
    require_passkey_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: passkey login/options/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return Status(429, {"error": "Too many attempts. Please try again later."})

    # If no credentials exist, don't issue a challenge — the browser would show
    # confusing hardware-key / QR prompts with nothing to match against.
    if not WebAuthnCredential.objects.exists():
        return Status(200, {"no_credentials": True})

    options = generate_authentication_options(
        rp_id=_get_rp_id(request),
        user_verification=UserVerificationRequirement.REQUIRED,
    )

    request.session["webauthn_login_challenge"] = options.challenge.hex()
    request.session["webauthn_login_challenge_created_at"] = time.time()

    return Status(200, json.loads(options_to_json(options)))


@router.post("/login/verify/", response={200: dict, 401: dict, 429: dict})
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
def login_verify(request):
    """Verify authentication response and establish session."""
    require_passkey_mode(request)

    # Consume challenge BEFORE rate limit check to prevent replay (FR-011)
    challenge_hex = request.session.pop("webauthn_login_challenge", None)
    created_at = request.session.pop("webauthn_login_challenge_created_at", None)

    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: passkey login/verify/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return Status(429, {"error": "Too many attempts. Please try again later."})

    if not challenge_hex:
        return Status(401, {"error": "Authentication failed: no pending challenge"})

    # Reject expired challenges (FR-010: 5-minute window)
    if created_at and (time.time() - created_at) > 300:
        return Status(401, {"error": "Authentication failed: challenge expired"})

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return Status(401, {"error": "Authentication failed: invalid request body"})

    # Look up credential by credential_id
    raw_id = body.get("rawId", "")
    try:
        from webauthn.helpers import base64url_to_bytes

        credential_id_bytes = base64url_to_bytes(raw_id)
    except Exception:
        return Status(401, {"error": "Authentication failed"})

    try:
        credential = WebAuthnCredential.objects.select_related("user").get(credential_id=credential_id_bytes)
    except WebAuthnCredential.DoesNotExist:
        security_logger.warning(
            "Passkey login: unknown credential from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return Status(401, {"error": "Authentication failed"})

    if not credential.user.is_active:
        return Status(401, {"error": "Authentication failed"})

    try:
        verification = verify_authentication_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=_get_rp_id(request),
            expected_origin=_get_origin(request),
            credential_public_key=bytes(credential.public_key),
            credential_current_sign_count=credential.sign_count,
            require_user_verification=True,
        )
    except Exception as e:
        security_logger.warning(
            "Passkey login verification failed from %s: %s",
            request.META.get("REMOTE_ADDR"),
            str(e),
        )
        return Status(401, {"error": "Authentication failed"})

    # Check sign_count for cloned authenticator
    if verification.new_sign_count > 0 and verification.new_sign_count <= credential.sign_count:
        security_logger.warning(
            "Possible cloned authenticator: user_id=%s, sign_count went from %d to %d",
            credential.user_id,
            credential.sign_count,
            verification.new_sign_count,
        )
        return Status(401, {"error": "Authentication failed"})

    # Update credential
    credential.sign_count = verification.new_sign_count
    credential.last_used_at = timezone.now()
    credential.save(update_fields=["sign_count", "last_used_at"])

    login(request, credential.user, backend=_AUTH_BACKEND)
    request.session["profile_id"] = credential.user.profile.id

    security_logger.info(
        "Passkey login: user_id=%s from %s",
        credential.user_id,
        request.META.get("REMOTE_ADDR"),
    )

    return Status(200, passkey_user_profile_response(credential.user, credential.user.profile))


# --- Credential Management ---


@router.get("/credentials/", response={200: dict}, auth=SessionAuth())
def list_credentials(request):
    """List current user's registered passkeys."""
    require_passkey_mode(request)
    credentials = WebAuthnCredential.objects.filter(user=request.user).order_by("created_at")
    total = credentials.count()

    return Status(
        200,
        {
            "credentials": [
                {
                    "id": c.pk,
                    "created_at": c.created_at.isoformat(),
                    "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
                    "is_deletable": total > 1,
                }
                for c in credentials
            ]
        },
    )


@router.post("/credentials/add/options/", response={200: dict}, auth=SessionAuth())
def add_credential_options(request):
    """Generate registration options for adding an additional passkey."""
    require_passkey_mode(request)

    existing_creds = WebAuthnCredential.objects.filter(user=request.user)
    exclude = [PublicKeyCredentialDescriptor(id=bytes(c.credential_id)) for c in existing_creds]

    options = generate_registration_options(
        rp_id=_get_rp_id(request),
        rp_name=settings.WEBAUTHN_RP_NAME,
        user_name=request.user.username,
        user_id=request.user.pk.to_bytes(8, "big"),
        user_display_name=request.auth.name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.REQUIRED,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=exclude,
    )

    request.session["webauthn_add_challenge"] = options.challenge.hex()
    request.session["webauthn_add_challenge_created_at"] = time.time()

    return Status(200, json.loads(options_to_json(options)))


@router.post("/credentials/add/verify/", response={201: dict, 400: dict}, auth=SessionAuth())
def add_credential_verify(request):
    """Verify and store additional passkey for authenticated user."""
    require_passkey_mode(request)

    challenge_hex = request.session.pop("webauthn_add_challenge", None)
    created_at = request.session.pop("webauthn_add_challenge_created_at", None)
    if not challenge_hex:
        return Status(400, {"error": "No pending challenge"})

    # Reject expired challenges (FR-010: 5-minute window)
    if created_at and (time.time() - created_at) > 300:
        return Status(400, {"error": "Challenge expired"})

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return Status(400, {"error": "Invalid request body"})

    try:
        verification = verify_registration_response(
            credential=body,
            expected_challenge=bytes.fromhex(challenge_hex),
            expected_rp_id=_get_rp_id(request),
            expected_origin=_get_origin(request),
            require_user_verification=True,
        )
    except Exception as e:
        security_logger.warning(
            "Add credential verification failed for user_id=%s: %s",
            request.user.pk,
            str(e),
        )
        return Status(400, {"error": "Verification failed"})

    cred = WebAuthnCredential.objects.create(
        user=request.user,
        credential_id=verification.credential_id,
        public_key=verification.credential_public_key,
        sign_count=verification.sign_count,
        transports=body.get("transports"),
    )

    security_logger.info(
        "Passkey added: user_id=%s, credential_pk=%s",
        request.user.pk,
        cred.pk,
    )

    return Status(
        201,
        {
            "credential": {
                "id": cred.pk,
                "created_at": cred.created_at.isoformat(),
                "last_used_at": None,
                "is_deletable": True,
            }
        },
    )


@router.delete(
    "/credentials/{credential_id}/",
    response={200: dict, 400: dict, 404: dict},
    auth=SessionAuth(),
)
@transaction.atomic
def delete_credential(request, credential_id: int):
    """Delete a registered passkey."""
    require_passkey_mode(request)

    try:
        cred = WebAuthnCredential.objects.select_for_update().get(pk=credential_id, user=request.user)
    except WebAuthnCredential.DoesNotExist:
        return Status(404, {"error": "Credential not found"})

    total = WebAuthnCredential.objects.select_for_update().filter(user=request.user).count()
    if total <= 1:
        return Status(400, {"error": "Cannot delete your only passkey"})

    cred.delete()
    security_logger.info(
        "Passkey deleted: user_id=%s, credential_pk=%s",
        request.user.pk,
        credential_id,
    )
    return Status(200, {"message": "Passkey deleted"})
