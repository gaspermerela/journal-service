"""
Integration tests for authentication API routes.
Requires database connection.
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import db_service


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "hashed_password" not in data  # Should not expose password
    assert data["is_active"] is True


@pytest.mark.asyncio
async def test_register_user_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    """Test registration with duplicate email."""
    from app.schemas.auth import UserCreate

    # Create first user directly in database
    user_data = UserCreate(email="duplicate@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Try to register with same email
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "password": "AnotherPassword123!"
        }
    )

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_user_invalid_email(client: AsyncClient):
    """Test registration with invalid email format."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "not-an-email",
            "password": "SecurePassword123!"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_user_short_password(client: AsyncClient):
    """Test registration with password too short."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "short"
        }
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful login."""
    from app.schemas.auth import UserCreate

    # Create user
    user_data = UserCreate(email="logintest@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "logintest@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0
    assert len(data["refresh_token"]) > 0
    assert "user" in data
    assert data["user"]["email"] == "logintest@example.com"
    assert data["user"]["is_active"] is True
    assert "id" in data["user"]
    assert "created_at" in data["user"]
    assert "hashed_password" not in data["user"]


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, db_session: AsyncSession):
    """Test login with incorrect password."""
    from app.schemas.auth import UserCreate

    # Create user
    user_data = UserCreate(email="wrongpass@example.com", password="CorrectPassword123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Login with wrong password
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!"
        }
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_user_not_found(client: AsyncClient):
    """Test login with non-existent user."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test login with deactivated user account."""
    from app.schemas.auth import UserCreate

    # Create user
    user_data = UserCreate(email="inactive@example.com", password="Password123!")
    user = await db_service.create_user(db_session, user_data)

    # Deactivate user
    user.is_active = False
    await db_session.commit()

    # Try to login
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "inactive@example.com",
            "password": "Password123!"
        }
    )

    assert response.status_code == 403
    assert "deactivated" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token_success(client: AsyncClient, db_session: AsyncSession):
    """Test successful token refresh."""
    from app.schemas.auth import UserCreate

    # Create and login user
    user_data = UserCreate(email="refresh@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "refresh@example.com", "password": "Password123!"}
    )
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    # Wait 2 seconds to ensure new tokens have different exp timestamp
    await asyncio.sleep(2)

    # Refresh tokens
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # New tokens should be different due to different exp timestamp
    assert data["access_token"] != tokens["access_token"]
    assert data["refresh_token"] != tokens["refresh_token"]
    assert "user" in data
    assert data["user"]["email"] == "refresh@example.com"
    assert data["user"]["is_active"] is True
    assert "id" in data["user"]
    assert "created_at" in data["user"]


@pytest.mark.asyncio
async def test_refresh_token_invalid(client: AsyncClient):
    """Test token refresh with invalid token."""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"}
    )

    assert response.status_code == 401
    assert "Invalid or expired" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_using_access_token(client: AsyncClient, db_session: AsyncSession):
    """Test that access token cannot be used for refresh."""
    from app.schemas.auth import UserCreate

    # Create and login user
    user_data = UserCreate(email="wrongtype@example.com", password="Password123!")
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongtype@example.com", "password": "Password123!"}
    )
    tokens = login_response.json()
    access_token = tokens["access_token"]  # Use access token instead of refresh

    # Try to refresh with access token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_deleted_user(client: AsyncClient, db_session: AsyncSession):
    """Test token refresh when user has been deleted."""
    from app.schemas.auth import UserCreate

    # Create and login user
    user_data = UserCreate(email="todelete@example.com", password="Password123!")
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "todelete@example.com", "password": "Password123!"}
    )
    tokens = login_response.json()
    refresh_token = tokens["refresh_token"]

    # Delete user
    await db_session.delete(user)
    await db_session.commit()

    # Try to refresh token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )

    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_complete_auth_flow(client: AsyncClient):
    """Test complete authentication flow: register -> login -> refresh."""
    email = "flowtest@example.com"
    password = "FlowPassword123!"

    # 1. Register
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password}
    )
    assert register_response.status_code == 201

    # 2. Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Wait 2 seconds to ensure new tokens have different exp timestamp
    await asyncio.sleep(2)

    # 3. Refresh
    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()

    # Verify we got new tokens (should be different due to different exp timestamp)
    assert new_tokens["access_token"] != tokens["access_token"]
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
