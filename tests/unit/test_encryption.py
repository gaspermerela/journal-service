"""
Unit tests for encryption service.

Tests per-user encryption/decryption of sensitive data like API keys.
"""

import pytest
import uuid
from app.services.encryption import encrypt_notion_key, decrypt_notion_key, verify_encryption


def test_basic_encryption():
    """Test basic encrypt/decrypt functionality."""
    user_id = uuid.uuid4()
    test_api_key = "secret_test123abc"

    # Encrypt
    encrypted = encrypt_notion_key(test_api_key, user_id)
    assert encrypted
    assert encrypted != test_api_key  # Should be encrypted, not plaintext

    # Decrypt
    decrypted = decrypt_notion_key(encrypted, user_id)
    assert decrypted == test_api_key


def test_per_user_isolation():
    """Test that different users get different encrypted values."""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    same_api_key = "secret_same_key"

    # Encrypt same key for two different users
    encrypted1 = encrypt_notion_key(same_api_key, user1_id)
    encrypted2 = encrypt_notion_key(same_api_key, user2_id)

    # Different users should get different encrypted values
    assert encrypted1 != encrypted2

    # But both should decrypt correctly with their own user_id
    assert decrypt_notion_key(encrypted1, user1_id) == same_api_key
    assert decrypt_notion_key(encrypted2, user2_id) == same_api_key


def test_cross_user_decryption_fails():
    """Test that User A cannot decrypt User B's data."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()
    api_key = "secret_user_a"

    # User A encrypts their key
    encrypted = encrypt_notion_key(api_key, user_a_id)

    # User A can decrypt their own key
    assert decrypt_notion_key(encrypted, user_a_id) == api_key

    # User B cannot decrypt User A's key (should raise ValueError)
    with pytest.raises(ValueError, match="Failed to decrypt API key"):
        decrypt_notion_key(encrypted, user_b_id)


def test_verify_encryption():
    """Test the verify_encryption helper function."""
    user_id = uuid.uuid4()

    # Verify should return True for valid encryption/decryption
    assert verify_encryption("test_value", user_id) is True


def test_empty_api_key_raises_error():
    """Test that encrypting empty API key raises ValueError."""
    user_id = uuid.uuid4()

    with pytest.raises(ValueError, match="API key cannot be empty"):
        encrypt_notion_key("", user_id)

    with pytest.raises(ValueError, match="API key cannot be empty"):
        encrypt_notion_key("   ", user_id)  # Whitespace only


def test_empty_encrypted_key_raises_error():
    """Test that decrypting empty encrypted key raises ValueError."""
    user_id = uuid.uuid4()

    with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
        decrypt_notion_key("", user_id)

    with pytest.raises(ValueError, match="Encrypted key cannot be empty"):
        decrypt_notion_key("   ", user_id)  # Whitespace only


def test_invalid_encrypted_data_raises_error():
    """Test that decrypting invalid/corrupted data raises ValueError."""
    user_id = uuid.uuid4()

    # Try to decrypt garbage data
    with pytest.raises(ValueError, match="Failed to decrypt API key"):
        decrypt_notion_key("not_valid_encrypted_data", user_id)


def test_encryption_is_deterministic_per_user():
    """Test that encrypting the same value twice for the same user produces different results."""
    user_id = uuid.uuid4()
    api_key = "secret_test"

    # Encrypt twice
    encrypted1 = encrypt_notion_key(api_key, user_id)
    encrypted2 = encrypt_notion_key(api_key, user_id)

    # Should be different (Fernet includes timestamp/nonce)
    assert encrypted1 != encrypted2

    # But both should decrypt to the same value
    assert decrypt_notion_key(encrypted1, user_id) == api_key
    assert decrypt_notion_key(encrypted2, user_id) == api_key


def test_encryption_with_special_characters():
    """Test encryption handles special characters in API keys."""
    user_id = uuid.uuid4()
    api_keys = [
        "secret_with-dashes",
        "secret_with_underscores",
        "secret/with/slashes",
        "secret.with.dots",
        "secret:with:colons",
        "secret with spaces",
        "secret_with_émojis_🔐",
    ]

    for api_key in api_keys:
        encrypted = encrypt_notion_key(api_key, user_id)
        decrypted = decrypt_notion_key(encrypted, user_id)
        assert decrypted == api_key, f"Failed for: {api_key}"
