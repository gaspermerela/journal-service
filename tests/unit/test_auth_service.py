"""
Unit tests for authentication service.
"""
import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.services.auth import AuthService
from app.schemas.auth import UserCreate, UserLogin, Token
from app.models.user import User


@pytest.fixture
def auth_service():
    """Create AuthService instance."""
    return AuthService()


@pytest.fixture
def mock_db_session():
    """Create mock database session."""
    return AsyncMock()


@pytest.fixture
def sample_user():
    """Create a sample user for testing."""
    from datetime import datetime, timezone
    from app.models.user import UserRole
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        hashed_password="$2b$12$hashedpassword",
        is_active=True,
        role=UserRole.USER,
        created_at=datetime.now(timezone.utc)
    )
    return user


@pytest.mark.asyncio
async def test_register_user_success(auth_service, mock_db_session, sample_user):
    """Test successful user registration."""
    user_data = UserCreate(email="test@example.com", password="Password123!")

    with patch('app.services.auth.db_service.create_user', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = sample_user

        result = await auth_service.register_user(mock_db_session, user_data)

        assert result == sample_user
        mock_create.assert_called_once_with(mock_db_session, user_data)


@pytest.mark.asyncio
async def test_register_user_duplicate_email(auth_service, mock_db_session):
    """Test registration with duplicate email raises error."""
    user_data = UserCreate(email="duplicate@example.com", password="Password123!")

    with patch('app.services.auth.db_service.create_user', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = HTTPException(status_code=400, detail="Email already registered")

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(mock_db_session, user_data)

        assert exc_info.value.status_code == 400
        assert "Email already registered" in exc_info.value.detail


@pytest.mark.asyncio
async def test_register_user_database_error(auth_service, mock_db_session):
    """Test registration handles database errors."""
    user_data = UserCreate(email="test@example.com", password="Password123!")

    with patch('app.services.auth.db_service.create_user', new_callable=AsyncMock) as mock_create:
        mock_create.side_effect = Exception("Database error")

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(mock_db_session, user_data)

        assert exc_info.value.status_code == 500
        assert "Registration failed" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_user_success(auth_service, mock_db_session, sample_user):
    """Test successful user authentication."""
    login_data = UserLogin(email="test@example.com", password="Password123!")

    with patch('app.services.auth.db_service.get_user_by_email', new_callable=AsyncMock) as mock_get_user, \
         patch('app.services.auth.verify_password') as mock_verify, \
         patch('app.services.auth.create_access_token') as mock_access, \
         patch('app.services.auth.create_refresh_token') as mock_refresh:

        mock_get_user.return_value = sample_user
        mock_verify.return_value = True
        mock_access.return_value = "access_token_string"
        mock_refresh.return_value = "refresh_token_string"

        result = await auth_service.authenticate_user(mock_db_session, login_data)

        assert isinstance(result, Token)
        assert result.access_token == "access_token_string"
        assert result.refresh_token == "refresh_token_string"
        assert result.token_type == "bearer"
        assert result.user.id == sample_user.id
        assert result.user.email == sample_user.email
        assert result.user.is_active == sample_user.is_active

        mock_get_user.assert_called_once_with(mock_db_session, login_data.email)
        mock_verify.assert_called_once_with(login_data.password, sample_user.hashed_password)
        mock_access.assert_called_once_with(sample_user.id, sample_user.email)
        mock_refresh.assert_called_once_with(sample_user.id, sample_user.email)


@pytest.mark.asyncio
async def test_authenticate_user_not_found(auth_service, mock_db_session):
    """Test authentication with non-existent user."""
    login_data = UserLogin(email="notfound@example.com", password="Password123!")

    with patch('app.services.auth.db_service.get_user_by_email', new_callable=AsyncMock) as mock_get_user:
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(mock_db_session, login_data)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(auth_service, mock_db_session, sample_user):
    """Test authentication with incorrect password."""
    login_data = UserLogin(email="test@example.com", password="WrongPassword!")

    with patch('app.services.auth.db_service.get_user_by_email', new_callable=AsyncMock) as mock_get_user, \
         patch('app.services.auth.verify_password') as mock_verify:

        mock_get_user.return_value = sample_user
        mock_verify.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(mock_db_session, login_data)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in exc_info.value.detail


@pytest.mark.asyncio
async def test_authenticate_user_inactive(auth_service, mock_db_session):
    """Test authentication with inactive user."""
    from datetime import datetime, timezone
    inactive_user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        hashed_password="$2b$12$hashedpassword",
        is_active=False,
        created_at=datetime.now(timezone.utc)
    )
    login_data = UserLogin(email="inactive@example.com", password="Password123!")

    with patch('app.services.auth.db_service.get_user_by_email', new_callable=AsyncMock) as mock_get_user, \
         patch('app.services.auth.verify_password') as mock_verify:

        mock_get_user.return_value = inactive_user
        mock_verify.return_value = True

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.authenticate_user(mock_db_session, login_data)

        assert exc_info.value.status_code == 403
        assert "deactivated" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_refresh_access_token_success(auth_service, mock_db_session, sample_user):
    """Test successful token refresh."""
    refresh_token = "valid_refresh_token"

    from app.schemas.auth import TokenData
    token_data = TokenData(
        user_id=sample_user.id,
        email=sample_user.email,
        token_type="refresh"
    )

    with patch('app.services.auth.verify_token') as mock_verify, \
         patch('app.services.auth.db_service.get_user_by_id', new_callable=AsyncMock) as mock_get_user, \
         patch('app.services.auth.create_access_token') as mock_access, \
         patch('app.services.auth.create_refresh_token') as mock_refresh:

        mock_verify.return_value = token_data
        mock_get_user.return_value = sample_user
        mock_access.return_value = "new_access_token"
        mock_refresh.return_value = "new_refresh_token"

        result = await auth_service.refresh_access_token(mock_db_session, refresh_token)

        assert isinstance(result, Token)
        assert result.access_token == "new_access_token"
        assert result.refresh_token == "new_refresh_token"
        assert result.token_type == "bearer"
        assert result.user.id == sample_user.id
        assert result.user.email == sample_user.email
        assert result.user.is_active == sample_user.is_active

        mock_verify.assert_called_once_with(refresh_token, expected_type="refresh")
        mock_get_user.assert_called_once_with(mock_db_session, sample_user.id)


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_token(auth_service, mock_db_session):
    """Test token refresh with invalid token."""
    from jose import JWTError

    with patch('app.services.auth.verify_token') as mock_verify:
        mock_verify.side_effect = JWTError("Invalid token")

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(mock_db_session, "invalid_token")

        assert exc_info.value.status_code == 401
        assert "Invalid or expired" in exc_info.value.detail


@pytest.mark.asyncio
async def test_refresh_access_token_user_not_found(auth_service, mock_db_session):
    """Test token refresh when user doesn't exist."""
    user_id = uuid.uuid4()
    from app.schemas.auth import TokenData

    token_data = TokenData(
        user_id=user_id,
        email="test@example.com",
        token_type="refresh"
    )

    with patch('app.services.auth.verify_token') as mock_verify, \
         patch('app.services.auth.db_service.get_user_by_id', new_callable=AsyncMock) as mock_get_user:

        mock_verify.return_value = token_data
        mock_get_user.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(mock_db_session, "valid_token")

        assert exc_info.value.status_code == 401
        assert "User not found" in exc_info.value.detail


@pytest.mark.asyncio
async def test_refresh_access_token_inactive_user(auth_service, mock_db_session):
    """Test token refresh with inactive user."""
    from datetime import datetime, timezone
    inactive_user = User(
        id=uuid.uuid4(),
        email="inactive@example.com",
        hashed_password="$2b$12$hashedpassword",
        is_active=False,
        created_at=datetime.now(timezone.utc)
    )

    from app.schemas.auth import TokenData
    token_data = TokenData(
        user_id=inactive_user.id,
        email=inactive_user.email,
        token_type="refresh"
    )

    with patch('app.services.auth.verify_token') as mock_verify, \
         patch('app.services.auth.db_service.get_user_by_id', new_callable=AsyncMock) as mock_get_user:

        mock_verify.return_value = token_data
        mock_get_user.return_value = inactive_user

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(mock_db_session, "valid_token")

        assert exc_info.value.status_code == 403
        assert "deactivated" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_refresh_access_token_missing_user_id(auth_service, mock_db_session):
    """Test token refresh with token missing user_id."""
    from app.schemas.auth import TokenData

    token_data = TokenData(
        user_id=None,  # Missing user_id
        email="test@example.com",
        token_type="refresh"
    )

    with patch('app.services.auth.verify_token') as mock_verify:
        mock_verify.return_value = token_data

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_access_token(mock_db_session, "token")

        assert exc_info.value.status_code == 401
        assert "Invalid refresh token" in exc_info.value.detail
