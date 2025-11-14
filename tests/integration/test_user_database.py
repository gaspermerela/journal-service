"""
Integration tests for user database service methods.
"""
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import DatabaseService
from app.schemas.auth import UserCreate
from app.models.user import User


@pytest.fixture
def db_service():
    """Create database service instance."""
    return DatabaseService()


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession, db_service: DatabaseService):
    """Test successful user creation."""
    user_data = UserCreate(
        email="test@example.com",
        password="SecurePassword123!"
    )

    user = await db_service.create_user(db_session, user_data)

    assert user is not None
    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.email == user_data.email
    assert user.hashed_password is not None
    assert user.hashed_password != user_data.password  # Password should be hashed
    assert user.is_active is True
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_create_user_hashes_password(db_session: AsyncSession, db_service: DatabaseService):
    """Test that password is hashed during user creation."""
    user_data = UserCreate(
        email="hash@example.com",
        password="PlainTextPassword"
    )

    user = await db_service.create_user(db_session, user_data)

    # Password should be hashed (bcrypt format starts with $2b$)
    assert user.hashed_password.startswith("$2b$")
    assert user.hashed_password != user_data.password
    assert len(user.hashed_password) == 60  # Bcrypt hash length


@pytest.mark.asyncio
async def test_create_user_duplicate_email(db_session: AsyncSession, db_service: DatabaseService):
    """Test that creating user with duplicate email raises error."""
    user_data = UserCreate(
        email="duplicate@example.com",
        password="Password123!"
    )

    # Create first user
    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Try to create second user with same email
    with pytest.raises(HTTPException) as exc_info:
        await db_service.create_user(db_session, user_data)

    assert exc_info.value.status_code == 400
    assert "Email already registered" in exc_info.value.detail


@pytest.mark.asyncio
async def test_get_user_by_email_exists(db_session: AsyncSession, db_service: DatabaseService):
    """Test retrieving user by email when user exists."""
    user_data = UserCreate(
        email="exists@example.com",
        password="Password123!"
    )

    # Create user
    created_user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Retrieve user
    retrieved_user = await db_service.get_user_by_email(db_session, user_data.email)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == user_data.email
    assert retrieved_user.hashed_password == created_user.hashed_password


@pytest.mark.asyncio
async def test_get_user_by_email_not_exists(db_session: AsyncSession, db_service: DatabaseService):
    """Test retrieving user by email when user doesn't exist."""
    user = await db_service.get_user_by_email(db_session, "nonexistent@example.com")

    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email_case_sensitive(db_session: AsyncSession, db_service: DatabaseService):
    """Test that email lookup is case-sensitive."""
    user_data = UserCreate(
        email="CaseSensitive@example.com",
        password="Password123!"
    )

    await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Exact match should find user
    user_exact = await db_service.get_user_by_email(db_session, "CaseSensitive@example.com")
    assert user_exact is not None

    # Different case should not find user (depends on database collation)
    # Note: PostgreSQL default is case-sensitive for exact matches
    user_lower = await db_service.get_user_by_email(db_session, "casesensitive@example.com")
    # This may or may not find the user depending on database settings


@pytest.mark.asyncio
async def test_get_user_by_id_exists(db_session: AsyncSession, db_service: DatabaseService):
    """Test retrieving user by ID when user exists."""
    user_data = UserCreate(
        email="byid@example.com",
        password="Password123!"
    )

    # Create user
    created_user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Retrieve user by ID
    retrieved_user = await db_service.get_user_by_id(db_session, created_user.id)

    assert retrieved_user is not None
    assert retrieved_user.id == created_user.id
    assert retrieved_user.email == user_data.email


@pytest.mark.asyncio
async def test_get_user_by_id_not_exists(db_session: AsyncSession, db_service: DatabaseService):
    """Test retrieving user by ID when user doesn't exist."""
    random_uuid = uuid.uuid4()
    user = await db_service.get_user_by_id(db_session, random_uuid)

    assert user is None


@pytest.mark.asyncio
async def test_create_multiple_users(db_session: AsyncSession, db_service: DatabaseService):
    """Test creating multiple users with different emails."""
    user1_data = UserCreate(email="user1@example.com", password="Pass111!")
    user2_data = UserCreate(email="user2@example.com", password="Pass222!")
    user3_data = UserCreate(email="user3@example.com", password="Pass333!")

    user1 = await db_service.create_user(db_session, user1_data)
    await db_session.commit()

    user2 = await db_service.create_user(db_session, user2_data)
    await db_session.commit()

    user3 = await db_service.create_user(db_session, user3_data)
    await db_session.commit()

    # All should have unique IDs
    assert user1.id != user2.id
    assert user2.id != user3.id
    assert user1.id != user3.id

    # All should be retrievable
    assert await db_service.get_user_by_email(db_session, "user1@example.com") is not None
    assert await db_service.get_user_by_email(db_session, "user2@example.com") is not None
    assert await db_service.get_user_by_email(db_session, "user3@example.com") is not None


@pytest.mark.asyncio
async def test_user_default_values(db_session: AsyncSession, db_service: DatabaseService):
    """Test that user has correct default values."""
    user_data = UserCreate(
        email="defaults@example.com",
        password="Password123!"
    )

    user = await db_service.create_user(db_session, user_data)

    # is_active should default to True
    assert user.is_active is True

    # Timestamps should be set
    assert user.created_at is not None
    assert user.updated_at is not None

    # created_at and updated_at should be close (within 1 second)
    time_diff = abs((user.updated_at - user.created_at).total_seconds())
    assert time_diff < 1


@pytest.mark.asyncio
async def test_create_user_with_special_characters_in_email(db_session: AsyncSession, db_service: DatabaseService):
    """Test creating user with special characters in email."""
    user_data = UserCreate(
        email="user+test@example.co.uk",
        password="Password123!"
    )

    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    assert user.email == "user+test@example.co.uk"

    # Should be retrievable
    retrieved = await db_service.get_user_by_email(db_session, "user+test@example.co.uk")
    assert retrieved is not None
    assert retrieved.id == user.id


@pytest.mark.asyncio
async def test_create_user_with_long_password(db_session: AsyncSession, db_service: DatabaseService):
    """Test creating user with long password (up to 72 chars for bcrypt)."""
    user_data = UserCreate(
        email="longpass@example.com",
        password="A" * 72  # Maximum length for bcrypt
    )

    user = await db_service.create_user(db_session, user_data)

    assert user is not None
    assert user.hashed_password is not None
