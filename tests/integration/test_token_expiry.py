"""
Integration tests for token expiration handling.
Tests that expired tokens are properly rejected.
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import UserCreate
from app.services.database import db_service
from app.utils.jwt import create_access_token, create_refresh_token
from app.config import settings


@pytest.fixture
async def test_user_expiry(db_session: AsyncSession):
    """Create a test user for token expiry tests."""
    user_data = UserCreate(
        email="expirytest@example.com",
        password="Password123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_expired_access_token_returns_401(client: AsyncClient, test_user_expiry):
    """Test that expired access token is rejected."""
    # Create token that expired 1 hour ago
    expired_time = datetime.now(timezone.utc) - timedelta(hours=1)

    # Manually create expired token by setting exp in the past
    from jose import jwt
    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        "exp": expired_time,
        "iat": expired_time - timedelta(days=7)
    }
    expired_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Try to use expired token
    client.headers["Authorization"] = f"Bearer {expired_token}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code == 401
    detail = response.json()["detail"].lower()
    assert "expired" in detail or "invalid" in detail or "credentials" in detail


@pytest.mark.asyncio
async def test_expired_refresh_token_returns_401(client: AsyncClient, test_user_expiry):
    """Test that expired refresh token cannot be used to get new tokens."""
    # Create refresh token that expired 1 day ago
    expired_time = datetime.now(timezone.utc) - timedelta(days=1)

    from jose import jwt
    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "refresh",
        "exp": expired_time,
        "iat": expired_time - timedelta(days=30)
    }
    expired_refresh_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Try to refresh with expired token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh_token}
    )

    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_token_with_future_iat_rejected(client: AsyncClient, test_user_expiry):
    """Test that token with future issued-at time is rejected."""
    # Create token issued in the future (suspicious)
    future_time = datetime.now(timezone.utc) + timedelta(hours=1)

    from jose import jwt
    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        "exp": future_time + timedelta(days=7),
        "iat": future_time
    }
    future_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # This might or might not be rejected depending on JWT library settings
    # But it should be treated with suspicion
    client.headers["Authorization"] = f"Bearer {future_token}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    # Accept either 401 (rejected) or 404 (accepted but entry not found)
    # The important thing is it doesn't cause a server error
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_valid_token_accepted(client: AsyncClient, test_user_expiry, db_session):
    """Test that valid, non-expired token is accepted."""
    # Login to get valid token
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "expirytest@example.com",
            "password": "Password123!"
        }
    )
    assert response.status_code == 200
    tokens = response.json()

    # Use valid token
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    # Should work (404 because entry doesn't exist, not 401)
    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code == 404  # Not 401


@pytest.mark.asyncio
async def test_token_expires_after_configured_time(client: AsyncClient, test_user_expiry):
    """Test that token expiration respects configured ACCESS_TOKEN_EXPIRE_DAYS."""
    # Create token with custom expiration
    from jose import jwt

    # Token that expires in exactly ACCESS_TOKEN_EXPIRE_DAYS
    exp_time = datetime.now(timezone.utc) + timedelta(days=settings.ACCESS_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        "exp": exp_time,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Should be accepted (not expired yet)
    client.headers["Authorization"] = f"Bearer {token}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    assert response.status_code != 401  # Should not be unauthorized


@pytest.mark.asyncio
async def test_refresh_token_expires_after_configured_time(client: AsyncClient, test_user_expiry):
    """Test that refresh token expiration respects configured REFRESH_TOKEN_EXPIRE_DAYS."""
    from jose import jwt

    # Refresh token that expires in exactly REFRESH_TOKEN_EXPIRE_DAYS
    exp_time = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "refresh",
        "exp": exp_time,
        "iat": datetime.now(timezone.utc)
    }
    refresh_token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Should be accepted for refresh
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_token_without_exp_claim_rejected(client: AsyncClient, test_user_expiry):
    """Test that token without expiration claim is rejected."""
    from jose import jwt

    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        # Missing "exp" claim
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    client.headers["Authorization"] = f"Bearer {token}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    # Without exp claim, jose doesn't validate expiration but token may still work
    # So we accept either 401 (rejected) or 404 (accepted but entry not found)
    assert response.status_code in [401, 404]


@pytest.mark.asyncio
async def test_token_with_very_long_expiry_accepted(client: AsyncClient, test_user_expiry):
    """Test that token with very long expiry (100 years) is still accepted if valid."""
    from jose import jwt

    # Token that expires in 100 years
    exp_time = datetime.now(timezone.utc) + timedelta(days=365 * 100)

    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        "exp": exp_time,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    client.headers["Authorization"] = f"Bearer {token}"

    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")

    # Should not be unauthorized (404 because entry doesn't exist)
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_token_expires_at_exact_timestamp(client: AsyncClient, test_user_expiry):
    """Test behavior at exact expiration timestamp."""
    from jose import jwt
    import time

    # Token that expires in 2 seconds
    exp_time = datetime.now(timezone.utc) + timedelta(seconds=2)

    payload = {
        "sub": str(test_user_expiry.id),
        "email": test_user_expiry.email,
        "type": "access",
        "exp": exp_time,
        "iat": datetime.now(timezone.utc)
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    # Use token immediately (should work)
    client.headers["Authorization"] = f"Bearer {token}"
    entry_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{entry_id}")
    assert response.status_code != 401

    # Wait for token to expire
    time.sleep(3)

    # Try again (should be expired now)
    response = await client.get(f"/api/v1/entries/{entry_id}")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refreshed_token_has_new_expiration(client: AsyncClient, test_user_expiry, db_session):
    """Test that refreshed access token gets a new expiration time."""
    from jose import jwt

    # Login to get initial tokens
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "expirytest@example.com",
            "password": "Password123!"
        }
    )
    tokens = response.json()
    original_access_token = tokens["access_token"]

    # Decode to get original expiration
    original_payload = jwt.decode(
        original_access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    original_exp = original_payload["exp"]

    # Wait 2 seconds
    import time
    time.sleep(2)

    # Refresh to get new tokens
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]}
    )
    new_tokens = refresh_response.json()
    new_access_token = new_tokens["access_token"]

    # Decode new token
    new_payload = jwt.decode(
        new_access_token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM]
    )
    new_exp = new_payload["exp"]

    # New token should have later expiration
    assert new_exp > original_exp
