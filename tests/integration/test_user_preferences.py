"""
Integration tests for user preferences API endpoints and database operations.
"""
import uuid
import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient

from app.services.database import DatabaseService
from app.schemas.auth import UserCreate
from app.models.user_preference import UserPreference


@pytest.fixture
def db_service():
    """Create database service instance."""
    return DatabaseService()


# Database Service Tests
@pytest.mark.asyncio
async def test_get_user_preferences_creates_default(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that get_user_preferences creates default preferences if they don't exist."""
    # Create a user
    user_data = UserCreate(
        email="preferences@example.com",
        password="Password123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Get preferences (should create default)
    preferences = await db_service.get_user_preferences(db_session, user.id)

    assert preferences is not None
    assert preferences.user_id == user.id
    assert preferences.preferred_transcription_language == "auto"
    assert preferences.id is not None
    assert preferences.created_at is not None
    assert preferences.updated_at is not None


@pytest.mark.asyncio
async def test_get_user_preferences_returns_existing(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that get_user_preferences returns existing preferences."""
    # Create a user
    user_data = UserCreate(
        email="existing_prefs@example.com",
        password="Password123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Get preferences first time (creates default)
    prefs1 = await db_service.get_user_preferences(db_session, user.id)
    await db_session.commit()

    # Get preferences second time (returns existing)
    prefs2 = await db_service.get_user_preferences(db_session, user.id)

    assert prefs1.id == prefs2.id
    assert prefs1.user_id == prefs2.user_id
    assert prefs1.preferred_transcription_language == prefs2.preferred_transcription_language


@pytest.mark.asyncio
async def test_update_user_preferences_success(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test successful update of user preferences."""
    # Create a user
    user_data = UserCreate(
        email="update_prefs@example.com",
        password="Password123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Update preferences
    updated_prefs = await db_service.update_user_preferences(
        db_session,
        user.id,
        preferred_transcription_language="es"
    )
    await db_session.commit()

    assert updated_prefs.preferred_transcription_language == "es"
    assert updated_prefs.user_id == user.id

    # Verify persistence
    retrieved_prefs = await db_service.get_user_preferences(db_session, user.id)
    assert retrieved_prefs.preferred_transcription_language == "es"


@pytest.mark.asyncio
async def test_update_user_preferences_creates_if_not_exists(
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that update creates preferences if they don't exist."""
    # Create a user
    user_data = UserCreate(
        email="create_on_update@example.com",
        password="Password123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()

    # Update preferences (should create them first)
    updated_prefs = await db_service.update_user_preferences(
        db_session,
        user.id,
        preferred_transcription_language="sl"
    )
    await db_session.commit()

    assert updated_prefs.preferred_transcription_language == "sl"
    assert updated_prefs.user_id == user.id


# API Endpoint Tests
@pytest.mark.asyncio
async def test_get_preferences_endpoint(authenticated_client: AsyncClient):
    """Test GET /api/v1/user/preferences endpoint."""
    response = await authenticated_client.get("/api/v1/user/preferences")

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "user_id" in data
    assert "preferred_transcription_language" in data
    assert data["preferred_transcription_language"] == "auto"  # Default
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_get_preferences_endpoint_unauthenticated(client: AsyncClient):
    """Test GET /api/v1/user/preferences fails without authentication."""
    response = await client.get("/api/v1/user/preferences")
    assert response.status_code == 403  # Forbidden when no auth header provided


@pytest.mark.asyncio
async def test_update_preferences_endpoint_success(authenticated_client: AsyncClient):
    """Test PUT /api/v1/user/preferences endpoint with valid data."""
    update_data = {
        "preferred_transcription_language": "en"
    }

    response = await authenticated_client.put(
        "/api/v1/user/preferences",
        json=update_data
    )

    assert response.status_code == 200
    data = response.json()
    assert data["preferred_transcription_language"] == "en"

    # Verify persistence
    get_response = await authenticated_client.get("/api/v1/user/preferences")
    assert get_response.status_code == 200
    get_data = get_response.json()
    assert get_data["preferred_transcription_language"] == "en"


@pytest.mark.asyncio
async def test_update_preferences_endpoint_invalid_language(authenticated_client: AsyncClient):
    """Test PUT /api/v1/user/preferences with invalid language code."""
    update_data = {
        "preferred_transcription_language": "invalid_lang"
    }

    response = await authenticated_client.put(
        "/api/v1/user/preferences",
        json=update_data
    )

    assert response.status_code == 422  # Validation error
    error_data = response.json()
    assert "detail" in error_data


@pytest.mark.asyncio
async def test_update_preferences_endpoint_unauthenticated(client: AsyncClient):
    """Test PUT /api/v1/user/preferences fails without authentication."""
    update_data = {
        "preferred_transcription_language": "es"
    }

    response = await client.put(
        "/api/v1/user/preferences",
        json=update_data
    )

    assert response.status_code == 403  # Forbidden when no auth header provided


@pytest.mark.asyncio
async def test_update_preferences_multiple_languages(authenticated_client: AsyncClient):
    """Test updating preferences to various valid languages."""
    test_languages = ["en", "es", "sl", "de", "fr", "auto"]

    for lang in test_languages:
        update_data = {"preferred_transcription_language": lang}
        response = await authenticated_client.put(
            "/api/v1/user/preferences",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()
        assert data["preferred_transcription_language"] == lang


@pytest.mark.asyncio
async def test_preferences_isolated_by_user(
    client: AsyncClient,
    db_session: AsyncSession,
    db_service: DatabaseService
):
    """Test that user preferences are properly isolated between users."""
    # Create two users
    user1_data = UserCreate(email="user1_isolation@example.com", password="Password123!")
    user2_data = UserCreate(email="user2_isolation@example.com", password="Password123!")

    user1 = await db_service.create_user(db_session, user1_data)
    user2 = await db_service.create_user(db_session, user2_data)
    await db_session.commit()

    # Update user1 preferences
    await db_service.update_user_preferences(
        db_session,
        user1.id,
        preferred_transcription_language="en"
    )

    # Update user2 preferences
    await db_service.update_user_preferences(
        db_session,
        user2.id,
        preferred_transcription_language="es"
    )
    await db_session.commit()

    # Verify isolation
    user1_prefs = await db_service.get_user_preferences(db_session, user1.id)
    user2_prefs = await db_service.get_user_preferences(db_session, user2.id)

    assert user1_prefs.preferred_transcription_language == "en"
    assert user2_prefs.preferred_transcription_language == "es"
    assert user1_prefs.id != user2_prefs.id
