"""Encryption utilities for sensitive data at rest."""

import base64
import hashlib

from django.conf import settings

try:
    from cryptography.fernet import Fernet, InvalidToken
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception


def _get_encryption_key() -> bytes:
    """Derive a Fernet key from Django's SECRET_KEY.

    Uses SHA-256 to create a consistent 32-byte key from the secret,
    then base64 encodes it for Fernet compatibility.
    """
    secret = settings.SECRET_KEY.encode()
    key = hashlib.sha256(secret).digest()
    return base64.urlsafe_b64encode(key)


def encrypt_value(plaintext: str) -> str:
    """Encrypt a string value.

    Args:
        plaintext: The string to encrypt.

    Returns:
        Base64-encoded encrypted string, prefixed with 'enc:'.
        Returns plaintext if cryptography is not available.
    """
    if not plaintext:
        return ''

    if not CRYPTOGRAPHY_AVAILABLE:
        # Fallback: store as-is if cryptography not installed
        return plaintext

    key = _get_encryption_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode())
    return f'enc:{encrypted.decode()}'


def decrypt_value(ciphertext: str) -> str:
    """Decrypt an encrypted string value.

    Args:
        ciphertext: The encrypted string (with 'enc:' prefix).

    Returns:
        The decrypted plaintext string.
        Returns original value if not encrypted or decryption fails.
    """
    if not ciphertext:
        return ''

    # Check if value is encrypted (has our prefix)
    if not ciphertext.startswith('enc:'):
        # Return as-is (legacy unencrypted value)
        return ciphertext

    if not CRYPTOGRAPHY_AVAILABLE:
        # Can't decrypt without cryptography - return empty for safety
        return ''

    try:
        key = _get_encryption_key()
        fernet = Fernet(key)
        encrypted_data = ciphertext[4:].encode()  # Remove 'enc:' prefix
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode()
    except (InvalidToken, ValueError):
        # If decryption fails, return empty string for safety
        return ''


def is_encrypted(value: str) -> bool:
    """Check if a value is already encrypted."""
    return value.startswith('enc:') if value else False
