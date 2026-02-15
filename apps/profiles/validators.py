"""Validation logic for user registration and profiles.

This module contains the source-of-truth validation rules used by both
the Django views and API endpoints. Client-side validation in the
frontend should mirror these rules for UX, but server-side validation
is always enforced.
"""

import re
from dataclasses import dataclass
from typing import Optional

from django.contrib.auth.models import User


@dataclass
class ValidationResult:
    """Result of a validation check."""

    is_valid: bool
    error: Optional[str] = None


# Validation constants - single source of truth
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 30
USERNAME_PATTERN = r"^[a-zA-Z0-9_]+$"
PASSWORD_MIN_LENGTH = 8


def validate_username(username: str) -> ValidationResult:
    """Validate username format and length.

    Rules:
    - Must be 3-30 characters
    - Can only contain letters, numbers, and underscores
    """
    if not username:
        return ValidationResult(False, "Username is required")

    username = username.strip()

    if len(username) < USERNAME_MIN_LENGTH:
        return ValidationResult(False, f"Username must be at least {USERNAME_MIN_LENGTH} characters")

    if len(username) > USERNAME_MAX_LENGTH:
        return ValidationResult(False, f"Username must be {USERNAME_MAX_LENGTH} characters or less")

    if not re.match(USERNAME_PATTERN, username):
        return ValidationResult(False, "Username can only contain letters, numbers, and underscores")

    return ValidationResult(True)


def validate_username_available(username: str) -> ValidationResult:
    """Check if username is available (case-insensitive)."""
    if User.objects.filter(username__iexact=username.strip()).exists():
        return ValidationResult(False, "Username already taken")
    return ValidationResult(True)


def validate_password(password: str) -> ValidationResult:
    """Validate password strength.

    Rules:
    - Must be at least 8 characters
    """
    if not password:
        return ValidationResult(False, "Password is required")

    if len(password) < PASSWORD_MIN_LENGTH:
        return ValidationResult(False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters")

    return ValidationResult(True)


def validate_password_confirmation(password: str, password_confirm: str) -> ValidationResult:
    """Validate that password and confirmation match."""
    if password != password_confirm:
        return ValidationResult(False, "Passwords do not match")
    return ValidationResult(True)


def validate_registration(
    username: str,
    password: str,
    password_confirm: str,
) -> ValidationResult:
    """Validate all registration fields.

    Returns the first validation error found, or success if all pass.
    """
    # Validate username format
    result = validate_username(username)
    if not result.is_valid:
        return result

    # Validate username availability
    result = validate_username_available(username)
    if not result.is_valid:
        return result

    # Validate password
    result = validate_password(password)
    if not result.is_valid:
        return result

    # Validate password confirmation
    result = validate_password_confirmation(password, password_confirm)
    if not result.is_valid:
        return result

    return ValidationResult(True)
