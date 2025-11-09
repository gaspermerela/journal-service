"""
Unit tests for password hashing utilities.
"""
import pytest
from app.utils.security import hash_password, verify_password


def test_hash_password_creates_hash():
    """Test that hash_password returns a bcrypt hash."""
    password = "SecurePassword123!"
    hashed = hash_password(password)

    # Bcrypt hashes start with $2b$ and are 60 characters
    assert hashed.startswith("$2b$")
    assert len(hashed) == 60
    assert hashed != password


def test_hash_password_different_hashes_for_same_password():
    """Test that hashing the same password twice produces different hashes (due to salt)."""
    password = "SecurePassword123!"
    hash1 = hash_password(password)
    hash2 = hash_password(password)

    # Hashes should be different due to random salt
    assert hash1 != hash2

    # But both should verify correctly
    assert verify_password(password, hash1)
    assert verify_password(password, hash2)


def test_verify_password_correct_password():
    """Test that verify_password returns True for correct password."""
    password = "MySecretPassword456"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_incorrect_password():
    """Test that verify_password returns False for incorrect password."""
    password = "MySecretPassword456"
    wrong_password = "WrongPassword789"
    hashed = hash_password(password)

    assert verify_password(wrong_password, hashed) is False


def test_verify_password_case_sensitive():
    """Test that password verification is case-sensitive."""
    password = "Password123"
    hashed = hash_password(password)

    # Different case should fail
    assert verify_password("password123", hashed) is False
    assert verify_password("PASSWORD123", hashed) is False

    # Exact match should succeed
    assert verify_password("Password123", hashed) is True


def test_hash_password_empty_string():
    """Test that empty string can be hashed (though not recommended)."""
    password = ""
    hashed = hash_password(password)

    assert hashed.startswith("$2b$")
    assert verify_password("", hashed) is True
    assert verify_password("anything", hashed) is False


def test_hash_password_unicode_characters():
    """Test that passwords with unicode characters are handled correctly."""
    password = "Pässwörd123!🔐"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True
    assert verify_password("Password123!🔐", hashed) is False


def test_hash_password_very_long_password():
    """Test that passwords up to 72 bytes can be hashed."""
    # Bcrypt has a 72-byte limit
    password = "a" * 72
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True

    # Test that passwords longer than 72 bytes raise ValueError
    very_long_password = "a" * 200
    try:
        hash_password(very_long_password)
        assert False, "Should have raised ValueError for password > 72 bytes"
    except ValueError as e:
        assert "72 bytes" in str(e)


def test_hash_password_special_characters():
    """Test that passwords with special characters are handled correctly."""
    password = "P@ssw0rd!#$%^&*()_+-=[]{}|;:',.<>?/~`"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_with_whitespace():
    """Test that passwords with whitespace are handled correctly."""
    password = "  Password With Spaces  "
    hashed = hash_password(password)

    # Exact match including whitespace
    assert verify_password("  Password With Spaces  ", hashed) is True

    # Without whitespace should fail
    assert verify_password("Password With Spaces", hashed) is False
