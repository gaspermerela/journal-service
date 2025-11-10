"""
Integration tests for cleanup routes.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cleaned_entry import CleanedEntry, CleanupStatus
from app.models.transcription import Transcription
from app.models.voice_entry import VoiceEntry
from app.models.user import User


@pytest.fixture
async def completed_transcription(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry
) -> Transcription:
    """Create a completed transcription for cleanup testing."""
    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=sample_voice_entry.id,
        transcribed_text="I had a dream about flying over mountains and oceans.",
        status="completed",
        model_used="whisper-base",
        language_code="en",
        transcription_started_at=datetime.utcnow(),
        transcription_completed_at=datetime.utcnow(),
        is_primary=True
    )

    db_session.add(transcription)
    await db_session.commit()
    await db_session.refresh(transcription)

    return transcription


@pytest.fixture
async def pending_transcription(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry
) -> Transcription:
    """Create a pending transcription (not completed yet)."""
    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=sample_voice_entry.id,
        transcribed_text=None,
        status="pending",
        model_used="whisper-base",
        language_code="en",
        is_primary=False
    )

    db_session.add(transcription)
    await db_session.commit()
    await db_session.refresh(transcription)

    return transcription


@pytest.fixture
async def sample_cleaned_entry(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry,
    completed_transcription: Transcription,
    test_user: User
) -> CleanedEntry:
    """Create a completed cleaned entry."""
    cleaned_entry = CleanedEntry(
        id=uuid.uuid4(),
        voice_entry_id=sample_voice_entry.id,
        transcription_id=completed_transcription.id,
        user_id=test_user.id,
        cleaned_text="I had a dream about flying over mountains and oceans.",
        analysis={
            "themes": ["flying", "nature", "adventure"],
            "emotions": ["excitement", "wonder"],
            "characters": [],
            "locations": ["mountains", "oceans"]
        },
        prompt_used="dream_cleanup",
        model_name="llama3.2:3b",
        status="completed",
        processing_started_at=datetime.utcnow(),
        processing_completed_at=datetime.utcnow()
    )

    db_session.add(cleaned_entry)
    await db_session.commit()
    await db_session.refresh(cleaned_entry)

    return cleaned_entry


class TestTriggerCleanup:
    """Tests for POST /api/v1/transcriptions/{id}/cleanup endpoint."""

    @pytest.mark.asyncio
    async def test_trigger_cleanup_success(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription,
        db_session: AsyncSession
    ):
        """Test successfully triggering cleanup for a completed transcription."""
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup"
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data  # cleanup_id
        assert data["transcription_id"] == str(completed_transcription.id)
        assert data["status"] == "pending"
        assert "message" in data

    @pytest.mark.asyncio
    async def test_trigger_cleanup_transcription_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test triggering cleanup for non-existent transcription."""
        fake_id = uuid.uuid4()

        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{fake_id}/cleanup"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_cleanup_transcription_not_completed(
        self,
        authenticated_client: AsyncClient,
        pending_transcription: Transcription
    ):
        """Test triggering cleanup for a transcription that's not completed yet."""
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{pending_transcription.id}/cleanup"
        )

        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_cleanup_no_text(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry
    ):
        """Test triggering cleanup for transcription with no text."""
        # Create completed transcription but with no text
        transcription = Transcription(
            id=uuid.uuid4(),
            entry_id=sample_voice_entry.id,
            transcribed_text=None,  # No text!
            status="completed",
            model_used="whisper-base",
            language_code="en",
            is_primary=False
        )

        db_session.add(transcription)
        await db_session.commit()

        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{transcription.id}/cleanup"
        )

        assert response.status_code == 400
        assert "no text" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_trigger_cleanup_unauthorized(
        self,
        client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test triggering cleanup without authentication."""
        response = await client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup"
        )

        assert response.status_code == 401


class TestGetCleanedEntry:
    """Tests for GET /api/v1/cleaned-entries/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_cleaned_entry_success(
        self,
        authenticated_client: AsyncClient,
        sample_cleaned_entry: CleanedEntry
    ):
        """Test successfully retrieving a cleaned entry."""
        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{sample_cleaned_entry.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(sample_cleaned_entry.id)
        assert data["status"] == "completed"
        assert data["cleaned_text"] is not None
        assert "analysis" in data
        assert "themes" in data["analysis"]

    @pytest.mark.asyncio
    async def test_get_cleaned_entry_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test retrieving non-existent cleaned entry."""
        fake_id = uuid.uuid4()

        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{fake_id}"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cleaned_entry_unauthorized(
        self,
        client: AsyncClient,
        sample_cleaned_entry: CleanedEntry
    ):
        """Test retrieving cleaned entry without authentication."""
        response = await client.get(
            f"/api/v1/cleaned-entries/{sample_cleaned_entry.id}"
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_cleaned_entry_different_user(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        completed_transcription: Transcription,
        sample_voice_entry: VoiceEntry
    ):
        """Test retrieving cleaned entry belonging to different user."""
        # Create another user
        from app.schemas.auth import UserCreate
        from app.services.database import db_service

        other_user = await db_service.create_user(
            db_session,
            UserCreate(email="other@example.com", password="Password123!")
        )
        await db_session.commit()

        # Create cleaned entry for other user
        cleaned_entry = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=other_user.id,  # Different user!
            cleaned_text="Text",
            model_name="llama3.2:3b",
            status="completed"
        )

        db_session.add(cleaned_entry)
        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{cleaned_entry.id}"
        )

        # Should not be able to access other user's cleaned entry
        assert response.status_code == 404


class TestGetCleanedEntriesByVoiceEntry:
    """Tests for GET /api/v1/entries/{id}/cleaned endpoint."""

    @pytest.mark.asyncio
    async def test_get_cleaned_entries_by_voice_entry_success(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        sample_cleaned_entry: CleanedEntry
    ):
        """Test successfully retrieving all cleaned entries for a voice entry."""
        response = await authenticated_client.get(
            f"/api/v1/entries/{sample_voice_entry.id}/cleaned"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["voice_entry_id"] == str(sample_voice_entry.id)

    @pytest.mark.asyncio
    async def test_get_cleaned_entries_empty_list(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry
    ):
        """Test retrieving cleaned entries when none exist."""
        response = await authenticated_client.get(
            f"/api/v1/entries/{sample_voice_entry.id}/cleaned"
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_cleaned_entries_voice_entry_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test retrieving cleaned entries for non-existent voice entry."""
        fake_id = uuid.uuid4()

        response = await authenticated_client.get(
            f"/api/v1/entries/{fake_id}/cleaned"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cleaned_entries_multiple_versions(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User
    ):
        """Test retrieving multiple cleanup attempts for same entry."""
        # Create multiple cleaned entries
        for i in range(3):
            cleaned_entry = CleanedEntry(
                id=uuid.uuid4(),
                voice_entry_id=sample_voice_entry.id,
                transcription_id=completed_transcription.id,
                user_id=test_user.id,
                cleaned_text=f"Version {i+1}",
                model_name="llama3.2:3b",
                status="completed"
            )
            db_session.add(cleaned_entry)

        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/entries/{sample_voice_entry.id}/cleaned"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        # Should be ordered by created_at descending
        assert data[0]["cleaned_text"] == "Version 3"


class TestCleanupProcessing:
    """Tests for background cleanup processing."""

    @pytest.mark.asyncio
    async def test_cleanup_status_transitions(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription,
        db_session: AsyncSession
    ):
        """Test that cleanup status transitions correctly."""
        # Mock LLM service
        with patch("app.routes.cleanup.LLMCleanupService") as mock_service_class:
            mock_service = AsyncMock()
            mock_service.cleanup_transcription.return_value = {
                "cleaned_text": "Cleaned",
                "analysis": {"themes": [], "emotions": [], "characters": [], "locations": []}
            }
            mock_service_class.return_value = mock_service

            # Trigger cleanup
            response = await authenticated_client.post(
                f"/api/v1/transcriptions/{completed_transcription.id}/cleanup"
            )

            cleanup_id = response.json()["id"]

            # Initial status should be pending
            assert response.json()["status"] == "pending"

            # Check status again (background task may have completed)
            status_response = await authenticated_client.get(
                f"/api/v1/cleaned-entries/{cleanup_id}"
            )

            assert status_response.status_code == 200
            # Status should be either pending, processing, or completed
            status = status_response.json()["status"]
            assert status in ["pending", "processing", "completed"]
