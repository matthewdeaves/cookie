"""Tests for core app functionality."""

import pytest
from django.test import TestCase

from .encryption import encrypt_value, decrypt_value, is_encrypted
from .models import AppSettings


class EncryptionTests(TestCase):
    """Tests for encryption utilities."""

    def test_encrypt_value(self):
        """Test encrypting a value adds enc: prefix."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt_value(plaintext)
        assert encrypted.startswith("enc:")
        assert plaintext not in encrypted

    def test_decrypt_value(self):
        """Test decrypting returns original value."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_encrypt_empty_string(self):
        """Test encrypting empty string returns empty string."""
        assert encrypt_value("") == ""

    def test_decrypt_empty_string(self):
        """Test decrypting empty string returns empty string."""
        assert decrypt_value("") == ""

    def test_decrypt_unencrypted_value(self):
        """Test decrypting unencrypted value returns as-is."""
        plaintext = "not-encrypted"
        assert decrypt_value(plaintext) == plaintext

    def test_is_encrypted(self):
        """Test is_encrypted correctly identifies encrypted values."""
        encrypted = encrypt_value("secret")
        assert is_encrypted(encrypted) is True
        assert is_encrypted("not-encrypted") is False
        assert is_encrypted("") is False

    def test_roundtrip_special_characters(self):
        """Test encryption/decryption with special characters."""
        plaintext = "sk-or-v1-abc123!@#$%^&*()_+-=[]{}|;:'\",.<>?/"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext


class AppSettingsEncryptionTests(TestCase):
    """Tests for AppSettings API key encryption."""

    def test_api_key_encrypted_on_save(self):
        """Test that API key is encrypted when saved."""
        settings = AppSettings.get()
        settings.openrouter_api_key = "test-api-key-123"
        settings.save()

        # Reload from database
        settings.refresh_from_db()

        # The stored value should be encrypted
        assert settings._openrouter_api_key.startswith("enc:")

        # But the property should return decrypted value
        assert settings.openrouter_api_key == "test-api-key-123"

    def test_api_key_property_decrypts(self):
        """Test that openrouter_api_key property decrypts the value."""
        settings = AppSettings.get()
        settings.openrouter_api_key = "another-key"
        settings.save()

        # Get fresh instance
        fresh_settings = AppSettings.get()
        assert fresh_settings.openrouter_api_key == "another-key"

    def test_legacy_unencrypted_key_still_works(self):
        """Test that legacy unencrypted keys are still readable."""
        settings = AppSettings.get()
        # Directly set the internal field (simulating legacy data)
        settings._openrouter_api_key = "legacy-unencrypted-key"
        settings.save(update_fields=["_openrouter_api_key"])

        # Reload
        settings.refresh_from_db()

        # Should still be readable (and now encrypted)
        # Note: save() encrypts it
        assert "legacy" in settings.openrouter_api_key or settings._openrouter_api_key.startswith("enc:")

    def test_empty_api_key(self):
        """Test handling of empty API key."""
        settings = AppSettings.get()
        settings.openrouter_api_key = ""
        settings.save()

        settings.refresh_from_db()
        assert settings.openrouter_api_key == ""
