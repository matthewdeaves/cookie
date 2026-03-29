"""Device code authorization flow API — only active in passkey mode."""

import logging

from django.conf import settings
from django.contrib.auth import login
from django.db import IntegrityError, transaction
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from ninja import Router, Schema

from apps.core.auth import SessionAuth
from apps.core.auth_helpers import passkey_user_profile_response, require_passkey_mode
from apps.core.models import DeviceCode, generate_device_code

security_logger = logging.getLogger("security")

router = Router(tags=["device"])

_AUTH_BACKEND = "django.contrib.auth.backends.ModelBackend"


class AuthorizeIn(Schema):
    code: str


@router.post("/code/", response={201: dict, 429: dict})
@ratelimit(key="ip", rate="10/h", method="POST", block=False)
def request_code(request):
    """Generate a new device pairing code."""
    require_passkey_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: device/code/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return 429, {"error": "Too many attempts. Please try again later."}

    # Ensure session exists
    if not request.session.session_key:
        request.session.create()

    session_key = request.session.session_key

    # Invalidate any existing pending codes for this session
    DeviceCode.objects.filter(session_key=session_key, status="pending").update(status="invalidated")

    # Clean up expired codes for this session
    DeviceCode.objects.filter(session_key=session_key, expires_at__lt=timezone.now()).exclude(
        status="authorized"
    ).delete()

    # Generate unique code with retry, handling DB-level unique constraint
    device_code = None
    for _ in range(10):
        code = generate_device_code()
        try:
            device_code = DeviceCode.objects.create(
                code=code,
                session_key=session_key,
                attempts_remaining=settings.DEVICE_CODE_MAX_ATTEMPTS,
                expires_at=timezone.now() + timezone.timedelta(seconds=settings.DEVICE_CODE_EXPIRY_SECONDS),
            )
            break
        except IntegrityError:
            continue

    if device_code is None:
        return 429, {"error": "Unable to generate code. Please try again."}

    security_logger.info(
        "Device code generated: session=%s from %s",
        session_key[:8],
        request.META.get("REMOTE_ADDR"),
    )

    return 201, {
        "code": device_code.code,
        "expires_in": settings.DEVICE_CODE_EXPIRY_SECONDS,
        "poll_interval": 5,
        "poll_url": "/api/auth/device/poll/",
    }


@router.get("/poll/", response={200: dict, 202: dict, 410: dict})
@ratelimit(key="ip", rate="180/h", method="GET", block=False)
@transaction.atomic
def poll_status(request):
    """Poll for device code authorization status."""
    require_passkey_mode(request)
    if getattr(request, "limited", False):
        return 410, {"status": "expired", "error": "Too many requests."}

    session_key = request.session.session_key
    if not session_key:
        return 410, {"status": "expired", "error": "No active code. Please request a new one."}

    try:
        device_code = (
            DeviceCode.objects.select_for_update(of=("self",))
            .select_related("authorizing_user")
            .get(session_key=session_key, status__in=["pending", "authorized"])
        )
    except DeviceCode.DoesNotExist:
        return 410, {"status": "expired", "error": "No active code. Please request a new one."}

    # Check expiry
    if device_code.is_expired and device_code.status == "pending":
        device_code.status = "expired"
        device_code.save(update_fields=["status"])
        return 410, {
            "status": "expired",
            "error": "Code has expired. Please request a new one.",
        }

    if device_code.status == "pending":
        return 202, {"status": "pending"}

    # Authorized — verify authorizing_user exists
    user = device_code.authorizing_user
    if user is None:
        device_code.status = "invalidated"
        device_code.save(update_fields=["status"])
        return 410, {"status": "expired", "error": "Authorization invalid. Please request a new code."}

    # Establish session for this device
    login(request, user, backend=_AUTH_BACKEND)
    request.session["profile_id"] = user.profile.id

    security_logger.info(
        "Device code consumed: user_id=%s, session=%s from %s",
        user.pk,
        session_key[:8],
        request.META.get("REMOTE_ADDR"),
    )

    # Mark code as consumed so it can't be re-polled
    device_code.status = "expired"
    device_code.save(update_fields=["status"])

    response = passkey_user_profile_response(user, user.profile)
    response["status"] = "authorized"
    return 200, response


@router.post("/authorize/", response={200: dict, 400: dict, 429: dict}, auth=SessionAuth())
@ratelimit(key="ip", rate="20/h", method="POST", block=False)
@transaction.atomic
def authorize_code(request, data: AuthorizeIn):
    """Authorize a pending device code (called by authenticated modern device)."""
    require_passkey_mode(request)
    if getattr(request, "limited", False):
        security_logger.warning(
            "Rate limit hit: device/authorize/ from %s",
            request.META.get("REMOTE_ADDR"),
        )
        return 429, {"error": "Too many attempts. Please try again later."}

    normalized_code = data.code.strip().upper()

    try:
        device_code = DeviceCode.objects.select_for_update().get(code=normalized_code, status="pending")
    except DeviceCode.DoesNotExist:
        security_logger.warning(
            "Device code authorize: invalid code from user_id=%s, ip=%s",
            request.user.pk,
            request.META.get("REMOTE_ADDR"),
        )
        return 400, {"error": "Invalid or expired code"}

    # Check expiry
    if device_code.is_expired:
        device_code.status = "expired"
        device_code.save(update_fields=["status"])
        return 400, {"error": "Invalid or expired code"}

    # Authorize the code
    device_code.status = "authorized"
    device_code.authorizing_user = request.user
    device_code.save(update_fields=["status", "authorizing_user"])

    security_logger.info(
        "Device code authorized by user_id=%s from %s",
        request.user.pk,
        request.META.get("REMOTE_ADDR"),
    )

    return 200, {"message": "Device authorized"}
