"""
Unit tests for JWT token utilities.
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.config import settings


def test_create_access_token():
    """Test that create_access_token generates a valid JWT."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    token = create_access_token(user_id, email)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify payload
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "access"
    assert "exp" in payload


def test_create_refresh_token():
    """Test that create_refresh_token generates a valid JWT."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    token = create_refresh_token(user_id, email)

    # Token should be a string
    assert isinstance(token, str)
    assert len(token) > 0

    # Decode and verify payload
    payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == str(user_id)
    assert payload["email"] == email
    assert payload["type"] == "refresh"
    assert "exp" in payload


def test_access_and_refresh_tokens_different():
    """Test that access and refresh tokens are different."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id, email)

    assert access_token != refresh_token


def test_token_expiration_time():
    """Test that tokens have correct expiration times."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    # Create access token
    access_token = create_access_token(user_id, email)
    access_payload = jwt.decode(access_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    access_exp = datetime.fromtimestamp(access_payload["exp"], tz=timezone.utc)

    # Create refresh token
    refresh_token = create_refresh_token(user_id, email)
    refresh_payload = jwt.decode(refresh_token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    refresh_exp = datetime.fromtimestamp(refresh_payload["exp"], tz=timezone.utc)

    # Check expiration times are in the future
    now = datetime.now(timezone.utc)
    assert access_exp > now
    assert refresh_exp > now

    # Check expiration times match configured values (allow 1 second tolerance)
    expected_access_exp = now + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)
    expected_refresh_exp = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    assert abs((access_exp - expected_access_exp).total_seconds()) < 2
    assert abs((refresh_exp - expected_refresh_exp).total_seconds()) < 2


def test_verify_token_valid_access():
    """Test that verify_token successfully verifies valid access token."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    token = create_access_token(user_id, email)
    token_data = verify_token(token, expected_type="access")

    assert token_data.user_id == user_id
    assert token_data.email == email
    assert token_data.token_type == "access"


def test_verify_token_valid_refresh():
    """Test that verify_token successfully verifies valid refresh token."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    token = create_refresh_token(user_id, email)
    token_data = verify_token(token, expected_type="refresh")

    assert token_data.user_id == user_id
    assert token_data.email == email
    assert token_data.token_type == "refresh"


def test_verify_token_wrong_type():
    """Test that verify_token rejects token with wrong type."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    # Create access token but verify as refresh
    access_token = create_access_token(user_id, email)

    with pytest.raises(JWTError) as exc_info:
        verify_token(access_token, expected_type="refresh")

    assert "Invalid token type" in str(exc_info.value)
    assert "expected refresh" in str(exc_info.value)
    assert "got access" in str(exc_info.value)


def test_verify_token_invalid_signature():
    """Test that verify_token rejects token with invalid signature."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    # Create token with wrong secret
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "type": "access"
    }
    invalid_token = jwt.encode(to_encode, "wrong-secret-key", algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(JWTError) as exc_info:
        verify_token(invalid_token)

    assert "Token verification failed" in str(exc_info.value)


def test_verify_token_expired():
    """Test that verify_token rejects expired token."""
    user_id = uuid.uuid4()
    email = "test@example.com"

    # Create token that expired 1 day ago
    to_encode = {
        "sub": str(user_id),
        "email": email,
        "exp": datetime.now(timezone.utc) - timedelta(days=1),
        "type": "access"
    }
    expired_token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(JWTError) as exc_info:
        verify_token(expired_token)

    assert "Token verification failed" in str(exc_info.value)


def test_verify_token_missing_subject():
    """Test that verify_token rejects token with missing subject."""
    email = "test@example.com"

    # Create token without 'sub' claim
    to_encode = {
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "type": "access"
    }
    invalid_token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(JWTError) as exc_info:
        verify_token(invalid_token)

    assert "Invalid token payload" in str(exc_info.value)


def test_verify_token_missing_email():
    """Test that verify_token rejects token with missing email."""
    user_id = uuid.uuid4()

    # Create token without 'email' claim
    to_encode = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=1),
        "type": "access"
    }
    invalid_token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(JWTError) as exc_info:
        verify_token(invalid_token)

    assert "Invalid token payload" in str(exc_info.value)


def test_verify_token_malformed():
    """Test that verify_token rejects malformed token."""
    malformed_token = "this.is.not.a.valid.jwt.token"

    with pytest.raises(JWTError) as exc_info:
        verify_token(malformed_token)

    assert "Token verification failed" in str(exc_info.value)


def test_verify_token_empty_string():
    """Test that verify_token rejects empty token string."""
    with pytest.raises(JWTError) as exc_info:
        verify_token("")

    assert "Token verification failed" in str(exc_info.value)


def test_token_roundtrip():
    """Test creating and verifying token in a roundtrip."""
    user_id = uuid.uuid4()
    email = "roundtrip@example.com"

    # Create token
    token = create_access_token(user_id, email)

    # Verify it
    token_data = verify_token(token, expected_type="access")

    # Should get back the same data
    assert token_data.user_id == user_id
    assert token_data.email == email


def test_different_users_different_tokens():
    """Test that different users get different tokens."""
    user1_id = uuid.uuid4()
    user2_id = uuid.uuid4()
    email1 = "user1@example.com"
    email2 = "user2@example.com"

    token1 = create_access_token(user1_id, email1)
    token2 = create_access_token(user2_id, email2)

    assert token1 != token2

    # Verify each token returns correct user data
    data1 = verify_token(token1)
    data2 = verify_token(token2)

    assert data1.user_id == user1_id
    assert data1.email == email1
    assert data2.user_id == user2_id
    assert data2.email == email2
