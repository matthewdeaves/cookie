"""Transient email verification service.

Email addresses are NEVER stored — they are held in memory only for the
duration of the HTTP request that sends the verification email.
"""

import logging

from django.conf import settings
from django.core.mail import send_mail
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

VERIFICATION_MAX_AGE = 7200  # 2 hours in seconds

_signer = TimestampSigner(salt="email-verification")


def generate_verification_token(user_id: int) -> str:
    """Generate a signed, timestamped token encoding the user's PK."""
    return _signer.sign(str(user_id))


def validate_verification_token(token: str) -> int | None:
    """Validate and unsign a verification token.

    Returns the user_id if valid, None if expired/tampered.
    """
    try:
        value = _signer.unsign(token, max_age=VERIFICATION_MAX_AGE)
        return int(value)
    except (BadSignature, SignatureExpired, ValueError):
        return None


def send_verification_email(user_id: int, email: str) -> None:
    """Send a verification email. The email parameter is transient — not stored.

    Args:
        user_id: The user's primary key (encoded in the token).
        email: The recipient email address (used only for sending, then discarded).
    """
    token = generate_verification_token(user_id)
    verify_url = f"{settings.SITE_URL}/api/auth/verify-email/?token={token}"

    context = {"verify_url": verify_url, "expiry_hours": 2}

    text_body = render_to_string("core/verification_email.txt", context)
    html_body = render_to_string("core/verification_email.html", context)

    send_mail(
        subject="Verify your Cookie account",
        message=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        html_message=html_body,
        fail_silently=False,
    )
    # email parameter goes out of scope here — never stored
    logger.info("Verification email sent for user_id=%s", user_id)
