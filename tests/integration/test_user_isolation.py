"""
Integration tests for user isolation.
Tests that users can only access their own data.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.user import User
from app.schemas.auth import UserCreate
from app.services.database import db_service


@pytest.fixture
async def user_a(db_session: AsyncSession) -> User:
    """Create first test user (User A)."""
    user_data = UserCreate(
        email="user_a@example.com",
        password="PasswordA123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()
    await db_session.refresh(user)

    # Disable encryption for tests (encryption service not available)
    user_prefs = await db_service.get_user_preferences(db_session, user.id)
    user_prefs.encryption_enabled = False
    await db_session.commit()

    return user


@pytest.fixture
async def user_b(db_session: AsyncSession) -> User:
    """Create second test user (User B)."""
    user_data = UserCreate(
        email="user_b@example.com",
        password="PasswordB123!"
    )
    user = await db_service.create_user(db_session, user_data)
    await db_session.commit()
    await db_session.refresh(user)

    # Disable encryption for tests (encryption service not available)
    user_prefs = await db_service.get_user_preferences(db_session, user.id)
    user_prefs.encryption_enabled = False
    await db_session.commit()

    return user


@pytest.fixture
async def authenticated_client_a(client: AsyncClient, user_a: User) -> AsyncClient:
    """Create authenticated client for User A."""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user_a@example.com",
            "password": "PasswordA123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Create a copy of headers to avoid conflicts
    client.headers = client.headers.copy()
    client.headers["Authorization"] = f"Bearer {tokens['access_token']}"
    yield client

    # Clean up
    client.headers.pop("Authorization", None)


@pytest.fixture
async def authenticated_client_b(client: AsyncClient, user_b: User, authenticated_client_a: AsyncClient) -> AsyncClient:
    """Create authenticated client for User B."""
    # Get a fresh client by logging in again
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user_b@example.com",
            "password": "PasswordB123!"
        }
    )
    assert login_response.status_code == 200
    tokens = login_response.json()

    # Create new headers to avoid overwriting client_a
    from httpx import AsyncClient as HttpxAsyncClient, ASGITransport
    from app.main import app

    # Create a separate client instance for user B
    async with HttpxAsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"Authorization": f"Bearer {tokens['access_token']}"}
    ) as client_b:
        yield client_b


@pytest.fixture
async def user_a_entry(db_session: AsyncSession, user_a: User, test_storage_path) -> VoiceEntry:
    """Create a voice entry belonging to User A."""
    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="user_a_recording.mp3",
        saved_filename="saved_a.mp3",
        file_path=str(test_storage_path / "user_a.mp3"),
        user_id=user_a.id
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    return entry


@pytest.fixture
async def user_b_entry(db_session: AsyncSession, user_b: User, test_storage_path) -> VoiceEntry:
    """Create a voice entry belonging to User B."""
    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="user_b_recording.mp3",
        saved_filename="saved_b.mp3",
        file_path=str(test_storage_path / "user_b.mp3"),
        user_id=user_b.id
    )
    db_session.add(entry)
    await db_session.commit()
    await db_session.refresh(entry)
    return entry


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_entry(
    authenticated_client_a: AsyncClient,
    user_b_entry: VoiceEntry
):
    """Test that User A cannot access User B's entry."""
    response = await authenticated_client_a.get(f"/api/v1/entries/{user_b_entry.id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_can_access_own_entry(
    authenticated_client_a: AsyncClient,
    user_a_entry: VoiceEntry
):
    """Test that User A can access their own entry."""
    response = await authenticated_client_a.get(f"/api/v1/entries/{user_a_entry.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(user_a_entry.id)
    assert data["original_filename"] == "user_a_recording.mp3"


@pytest.mark.asyncio
async def test_user_cannot_trigger_transcription_for_other_users_entry(
    authenticated_client_a: AsyncClient,
    user_b_entry: VoiceEntry,
    mock_transcription_service
):
    """Test that User A cannot trigger transcription for User B's entry."""
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    response = await authenticated_client_a.post(
        f"/api/v1/entries/{user_b_entry.id}/transcribe",
        json={"language": "en"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_can_trigger_transcription_for_own_entry(
    authenticated_client_a: AsyncClient,
    user_a_entry: VoiceEntry,
    mock_transcription_service
):
    """Test that User A can trigger transcription for their own entry."""
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    response = await authenticated_client_a.post(
        f"/api/v1/entries/{user_a_entry.id}/transcribe",
        json={"language": "en"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["entry_id"] == str(user_a_entry.id)


@pytest.mark.asyncio
async def test_user_cannot_access_other_users_transcription(
    authenticated_client_a: AsyncClient,
    db_session: AsyncSession,
    user_b_entry: VoiceEntry
):
    """Test that User A cannot access User B's transcription."""
    from datetime import datetime, timezone

    # Create transcription for User B's entry
    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=user_b_entry.id,
        transcribed_text="User B's transcription",
        status="completed",
        model_used="whisper-base",
        language_code="en",
        transcription_started_at=datetime.now(timezone.utc),
        transcription_completed_at=datetime.now(timezone.utc),
        is_primary=True
    )
    db_session.add(transcription)
    await db_session.commit()

    # User A tries to access it
    response = await authenticated_client_a.get(f"/api/v1/transcriptions/{transcription.id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_list_other_users_transcriptions(
    authenticated_client_a: AsyncClient,
    user_b_entry: VoiceEntry
):
    """Test that User A cannot list User B's transcriptions."""
    response = await authenticated_client_a.get(
        f"/api/v1/entries/{user_b_entry.id}/transcriptions"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_user_cannot_set_primary_for_other_users_transcription(
    authenticated_client_a: AsyncClient,
    db_session: AsyncSession,
    user_b_entry: VoiceEntry
):
    """Test that User A cannot set primary transcription for User B's entry."""
    from datetime import datetime, timezone

    # Create transcription for User B's entry
    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=user_b_entry.id,
        transcribed_text="User B's transcription",
        status="completed",
        model_used="whisper-base",
        language_code="en",
        transcription_started_at=datetime.now(timezone.utc),
        transcription_completed_at=datetime.now(timezone.utc),
        is_primary=False
    )
    db_session.add(transcription)
    await db_session.commit()

    # User A tries to set it as primary
    response = await authenticated_client_a.put(
        f"/api/v1/transcriptions/{transcription.id}/set-primary"
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_upload_associates_entry_with_correct_user(
    authenticated_client_a: AsyncClient,
    authenticated_client_b: AsyncClient,
    sample_mp3_path,
    db_session: AsyncSession
):
    """Test that uploaded entries are associated with the correct user."""
    # User A uploads
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("user_a.mp3", f, "audio/mpeg")}
        response_a = await authenticated_client_a.post("/api/v1/upload", files=files)

    assert response_a.status_code == 201
    entry_a_id = response_a.json()["id"]

    # User B uploads
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("user_b.mp3", f, "audio/mpeg")}
        response_b = await authenticated_client_b.post("/api/v1/upload", files=files)

    assert response_b.status_code == 201
    entry_b_id = response_b.json()["id"]

    # User A can access their own entry
    response = await authenticated_client_a.get(f"/api/v1/entries/{entry_a_id}")
    assert response.status_code == 200

    # User A cannot access User B's entry
    response = await authenticated_client_a.get(f"/api/v1/entries/{entry_b_id}")
    assert response.status_code == 404

    # User B can access their own entry
    response = await authenticated_client_b.get(f"/api/v1/entries/{entry_b_id}")
    assert response.status_code == 200

    # User B cannot access User A's entry
    response = await authenticated_client_b.get(f"/api/v1/entries/{entry_a_id}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_multiple_users_with_same_filename(
    authenticated_client_a: AsyncClient,
    authenticated_client_b: AsyncClient,
    sample_mp3_path
):
    """Test that multiple users can upload files with the same name."""
    filename = "same_name.mp3"

    # Both users upload file with same name
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": (filename, f, "audio/mpeg")}
        response_a = await authenticated_client_a.post("/api/v1/upload", files=files)

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": (filename, f, "audio/mpeg")}
        response_b = await authenticated_client_b.post("/api/v1/upload", files=files)

    # Both should succeed
    assert response_a.status_code == 201
    assert response_b.status_code == 201

    # Entries should have different IDs
    assert response_a.json()["id"] != response_b.json()["id"]

    # Both should preserve original filename
    assert response_a.json()["original_filename"] == filename
    assert response_b.json()["original_filename"] == filename
