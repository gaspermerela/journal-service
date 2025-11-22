"""
Integration tests for delete endpoints.
Tests all three delete operations: voice entries, transcriptions, and cleaned entries.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.transcription import Transcription
from app.models.user import User
from app.models.voice_entry import VoiceEntry
from app.schemas.auth import UserCreate
from app.services.database import db_service


# ============================================================================
# Fixtures for second user
# ============================================================================


@pytest.fixture
async def second_user(db_session: AsyncSession) -> User:
    """Create second test user."""
    user_data = UserCreate(
        email="seconduser@example.com",
        password="SecondPassword123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def authenticated_client_second_user(client: AsyncClient, second_user: User) -> AsyncClient:
    """Create authenticated client for second user."""
    from httpx import AsyncClient as HttpxAsyncClient, ASGITransport
    from app.main import app

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "seconduser@example.com",
            "password": "SecondPassword123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Create new client to avoid header conflicts
    second_client = HttpxAsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    )
    second_client.headers["Authorization"] = f"Bearer {tokens['access_token']}"

    yield second_client

    await second_client.aclose()


# ============================================================================
# Voice Entry Deletion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_entry_success(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    db_session: AsyncSession
):
    """Test successful deletion of a voice entry."""
    entry_id = sample_voice_entry.id

    # Delete the entry
    response = await authenticated_client.delete(f"/api/v1/entries/{entry_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Entry deleted successfully"
    assert data["deleted_id"] == str(entry_id)

    # Verify entry is deleted from database
    deleted_entry = await db_service.get_entry_by_id(db_session, entry_id)
    assert deleted_entry is None


@pytest.mark.asyncio
async def test_delete_entry_not_found(authenticated_client: AsyncClient):
    """Test deleting a non-existent entry returns 404."""
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.delete(f"/api/v1/entries/{non_existent_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_entry_invalid_uuid(authenticated_client: AsyncClient):
    """Test deleting with invalid UUID format returns 422."""
    response = await authenticated_client.delete("/api/v1/entries/invalid-uuid")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_delete_entry_requires_auth(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that delete requires authentication."""
    response = await client.delete(f"/api/v1/entries/{sample_voice_entry.id}")
    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


@pytest.mark.asyncio
async def test_delete_entry_cascades_to_children(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    db_session: AsyncSession
):
    """Test that deleting entry also deletes transcriptions."""
    entry_id = sample_voice_entry.id
    transcription_id = sample_transcription.id

    # Delete the entry
    response = await authenticated_client.delete(f"/api/v1/entries/{entry_id}")
    assert response.status_code == 200

    # Verify transcription is also deleted
    deleted_transcription = await db_service.get_transcription_by_id(db_session, transcription_id)
    assert deleted_transcription is None


@pytest.mark.asyncio
async def test_delete_entry_removes_audio_file(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry
):
    """Test that deleting entry attempts to remove audio file (file cleanup is best-effort)."""
    entry_id = sample_voice_entry.id

    # Delete the entry (file cleanup is handled by storage service in best-effort manner)
    response = await authenticated_client.delete(f"/api/v1/entries/{entry_id}")
    assert response.status_code == 200

    # The actual file deletion behavior is tested in unit tests for storage service


# ============================================================================
# Transcription Deletion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_transcription_success(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    db_session: AsyncSession
):
    """Test successful deletion of a transcription."""
    # Create two transcriptions for the entry
    from app.schemas.transcription import TranscriptionCreate

    trans1 = await db_service.create_transcription(
        db_session,
        TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed",
            model_used="whisper-large-v3",
            language_code="en",
            is_primary=True
        )
    )
    trans2 = await db_service.create_transcription(
        db_session,
        TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed",
            model_used="whisper-large-v3",
            language_code="en",
            is_primary=False
        )
    )
    await db_session.commit()

    # Delete the non-primary transcription
    response = await authenticated_client.delete(f"/api/v1/transcriptions/{trans2.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Transcription deleted successfully"
    assert data["deleted_id"] == str(trans2.id)

    # Verify transcription is deleted
    deleted_trans = await db_service.get_transcription_by_id(db_session, trans2.id)
    assert deleted_trans is None

    # Verify primary transcription still exists
    primary_trans = await db_service.get_transcription_by_id(db_session, trans1.id)
    assert primary_trans is not None


@pytest.mark.asyncio
async def test_delete_transcription_prevents_deleting_only_transcription(
    authenticated_client: AsyncClient,
    sample_transcription: Transcription
):
    """Test that deleting the only transcription is prevented."""
    # sample_transcription is the only transcription for its entry
    response = await authenticated_client.delete(f"/api/v1/transcriptions/{sample_transcription.id}")

    assert response.status_code == 409
    data = response.json()
    assert "only transcription" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_transcription_not_found(authenticated_client: AsyncClient):
    """Test deleting a non-existent transcription returns 404."""
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.delete(f"/api/v1/transcriptions/{non_existent_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_transcription_requires_auth(
    client: AsyncClient,
    sample_transcription: Transcription
):
    """Test that delete requires authentication."""
    response = await client.delete(f"/api/v1/transcriptions/{sample_transcription.id}")
    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


@pytest.mark.asyncio
async def test_delete_transcription_user_isolation(
    authenticated_client: AsyncClient,
    authenticated_client_second_user: AsyncClient,
    sample_voice_entry: VoiceEntry,
    db_session: AsyncSession
):
    """Test that users cannot delete other users' transcriptions."""
    from app.schemas.transcription import TranscriptionCreate

    # Create a transcription for user 1
    trans = await db_service.create_transcription(
        db_session,
        TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed",
            model_used="whisper-large-v3",
            language_code="en",
            is_primary=False
        )
    )
    await db_session.commit()

    # User 2 tries to delete user 1's transcription
    response = await authenticated_client_second_user.delete(f"/api/v1/transcriptions/{trans.id}")

    assert response.status_code == 404  # Returns 404 for security


# ============================================================================
# Cleaned Entry Deletion Tests
# ============================================================================


@pytest.mark.asyncio
async def test_delete_cleaned_entry_success(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    test_user: User,
    db_session: AsyncSession
):
    """Test successful deletion of a cleaned entry."""
    # Create a cleaned entry
    from app.config import settings
    cleaned_entry = await db_service.create_cleaned_entry(
        db_session,
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        model_name=settings.OLLAMA_MODEL
    )
    await db_session.commit()

    # Delete the cleaned entry
    response = await authenticated_client.delete(f"/api/v1/cleaned-entries/{cleaned_entry.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Cleaned entry deleted successfully"
    assert data["deleted_id"] == str(cleaned_entry.id)

    # Verify cleaned entry is deleted
    deleted_entry = await db_service.get_cleaned_entry_by_id(db_session, cleaned_entry.id)
    assert deleted_entry is None


@pytest.mark.asyncio
async def test_delete_cleaned_entry_not_found(authenticated_client: AsyncClient):
    """Test deleting a non-existent cleaned entry returns 404."""
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.delete(f"/api/v1/cleaned-entries/{non_existent_id}")

    assert response.status_code == 404
    data = response.json()
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_delete_cleaned_entry_requires_auth(
    client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    test_user: User,
    db_session: AsyncSession
):
    """Test that delete requires authentication."""
    from app.config import settings
    cleaned_entry = await db_service.create_cleaned_entry(
        db_session,
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        model_name=settings.OLLAMA_MODEL
    )
    await db_session.commit()

    response = await client.delete(f"/api/v1/cleaned-entries/{cleaned_entry.id}")
    assert response.status_code in [401, 403]  # Either Unauthorized or Forbidden


@pytest.mark.asyncio
async def test_delete_cleaned_entry_user_isolation(
    authenticated_client: AsyncClient,
    authenticated_client_second_user: AsyncClient,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    test_user: User,
    db_session: AsyncSession
):
    """Test that users cannot delete other users' cleaned entries."""
    from app.config import settings
    cleaned_entry = await db_service.create_cleaned_entry(
        db_session,
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        model_name=settings.OLLAMA_MODEL
    )
    await db_session.commit()

    # User 2 tries to delete user 1's cleaned entry
    response = await authenticated_client_second_user.delete(f"/api/v1/cleaned-entries/{cleaned_entry.id}")

    assert response.status_code == 404  # Returns 404 for security


@pytest.mark.asyncio
async def test_delete_cleaned_entry_no_restrictions(
    authenticated_client: AsyncClient,
    sample_voice_entry: VoiceEntry,
    sample_transcription: Transcription,
    test_user: User,
    db_session: AsyncSession
):
    """Test that any cleaned entry can be deleted (no restriction like transcriptions)."""
    from app.config import settings

    # Create multiple cleaned entries
    cleaned1 = await db_service.create_cleaned_entry(
        db_session,
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        model_name=settings.OLLAMA_MODEL
    )
    cleaned2 = await db_service.create_cleaned_entry(
        db_session,
        voice_entry_id=sample_voice_entry.id,
        transcription_id=sample_transcription.id,
        user_id=test_user.id,
        model_name=settings.OLLAMA_MODEL
    )
    await db_session.commit()

    # Delete both should succeed
    response1 = await authenticated_client.delete(f"/api/v1/cleaned-entries/{cleaned1.id}")
    assert response1.status_code == 200

    response2 = await authenticated_client.delete(f"/api/v1/cleaned-entries/{cleaned2.id}")
    assert response2.status_code == 200
