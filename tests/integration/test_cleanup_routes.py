"""
Integration tests for cleanup routes.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, patch, Mock

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cleaned_entry import CleanedEntry, CleanupStatus
from app.models.transcription import Transcription
from app.models.voice_entry import VoiceEntry
from app.models.user import User
from app.models.prompt_template import PromptTemplate


@pytest.fixture
async def sample_prompt_template(
    db_session: AsyncSession
) -> PromptTemplate:
    """Create a sample prompt template for testing."""
    prompt_template = PromptTemplate(
        name="Dream Analysis v1",
        entry_type="dream",
        prompt_text="Analyze this dream: {transcription_text}\n\n{output_format}",
        description="Standard dream analysis prompt",
        is_active=False,  # Not active to avoid unique constraint issues in tests
        version=1
    )

    db_session.add(prompt_template)
    await db_session.commit()
    await db_session.refresh(prompt_template)

    return prompt_template


@pytest.fixture
async def completed_transcription(
    db_session: AsyncSession,
    sample_voice_entry: VoiceEntry,
    encryption_service
) -> Transcription:
    """Create a completed transcription for cleanup testing with proper encryption."""
    # Encrypt the transcribed text properly so DEK is created
    plaintext = "I had a vivid dream about flying over mountains and vast oceans. The scenery was beautiful."
    encrypted_text = await encryption_service.encrypt_data(
        db_session,
        plaintext,
        sample_voice_entry.id,
        sample_voice_entry.user_id
    )

    transcription = Transcription(
        id=uuid.uuid4(),
        entry_id=sample_voice_entry.id,
        transcribed_text=encrypted_text,
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
    test_user: User,
    sample_prompt_template: PromptTemplate,
    encryption_service
) -> CleanedEntry:
    """Create a completed cleaned entry with proper encryption."""
    import json

    # Properly encrypt cleaned_text and analysis using the encryption service
    cleaned_text_plain = "This is the cleaned and processed dream content about flying over mountains."
    analysis_dict = {
        "themes": ["flying", "nature", "adventure"],
        "emotions": ["excitement", "wonder"],
        "characters": [],
        "locations": ["mountains", "oceans"]
    }

    encrypted_cleaned_text = await encryption_service.encrypt_data(
        db_session,
        cleaned_text_plain,
        sample_voice_entry.id,
        test_user.id
    )
    encrypted_analysis = await encryption_service.encrypt_data(
        db_session,
        json.dumps(analysis_dict),
        sample_voice_entry.id,
        test_user.id
    )

    cleaned_entry = CleanedEntry(
        id=uuid.uuid4(),
        voice_entry_id=sample_voice_entry.id,
        transcription_id=completed_transcription.id,
        user_id=test_user.id,
        cleaned_text=encrypted_cleaned_text,
        analysis=encrypted_analysis,
        prompt_template_id=sample_prompt_template.id,
        model_name="llama3.2:3b",
        processing_started_at=datetime.utcnow(),
        processing_completed_at=datetime.utcnow()
    )
    # Set status to completed (using string value, not enum)
    cleaned_entry.status = "completed"

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

        assert response.status_code in [401, 403]  # Either unauthorized or forbidden


class TestGetCleanedEntry:
    """Tests for GET /api/v1/cleaned-entries/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_cleaned_entry_success(
        self,
        authenticated_client: AsyncClient,
        sample_cleaned_entry: CleanedEntry,
        sample_prompt_template: PromptTemplate
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
        # Verify prompt template fields
        assert data["prompt_template_id"] == sample_prompt_template.id
        assert data["prompt_name"] == "Dream Analysis v1"
        assert data["prompt_description"] == "Standard dream analysis prompt"

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

        assert response.status_code in [401, 403]  # Either unauthorized or forbidden

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
            cleaned_text=b"encrypted_text",
            model_name="llama3.2:3b"
        )
        cleaned_entry.status = "completed"

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
        sample_cleaned_entry: CleanedEntry,
        sample_prompt_template: PromptTemplate
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
        # Verify prompt template fields are included
        assert "prompt_template_id" in data[0]
        assert "prompt_name" in data[0]
        assert "prompt_description" in data[0]
        assert data[0]["prompt_template_id"] == sample_prompt_template.id
        assert data[0]["prompt_name"] == "Dream Analysis v1"

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
        test_user: User,
        encryption_service
    ):
        """Test retrieving multiple cleanup attempts for same entry."""
        # Create multiple cleaned entries (only last one is primary due to constraint)
        # Properly encrypt the cleaned_text using the encryption service
        for i in range(3):
            encrypted_text = await encryption_service.encrypt_data(
                db_session,
                f"Version {i+1}",
                sample_voice_entry.id,
                test_user.id
            )
            cleaned_entry = CleanedEntry(
                id=uuid.uuid4(),
                voice_entry_id=sample_voice_entry.id,
                transcription_id=completed_transcription.id,
                user_id=test_user.id,
                cleaned_text=encrypted_text,
                model_name="llama3.2:3b",
                is_primary=(i == 2)  # Only the last one is primary (one primary per voice_entry)
            )
            cleaned_entry.status = "completed"
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
        db_session: AsyncSession,
        mock_llm_cleanup_service
    ):
        """Test that cleanup status transitions correctly."""
        # Trigger cleanup
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup"
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        cleanup_id = data["id"]

        # Initial status should be pending
        assert data["status"] == "pending"

        # Check status again (background task may have completed)
        status_response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{cleanup_id}"
        )

        assert status_response.status_code == 200
        # Status should be either pending, processing, or completed
        status = status_response.json()["status"]
        assert status in ["pending", "processing", "completed"]


class TestSetPrimaryCleanup:
    """Tests for setting cleanup as primary."""

    @pytest.mark.asyncio
    async def test_set_primary_cleanup_success(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User,
        db_session: AsyncSession,
        sample_prompt_template: PromptTemplate
    ):
        """Test setting a cleanup as primary."""
        from app.models.cleaned_entry import CleanedEntry, CleanupStatus
        import uuid

        # Create two completed cleanups
        cleanup1 = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"First cleanup",
            model_name="llama3.2:3b",
            prompt_template_id=sample_prompt_template.id,
            is_primary=True
        )
        cleanup1.status = CleanupStatus.COMPLETED

        cleanup2 = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Second cleanup",
            model_name="llama3.2:3b",
            prompt_template_id=sample_prompt_template.id,
            is_primary=False
        )
        cleanup2.status = CleanupStatus.COMPLETED

        db_session.add_all([cleanup1, cleanup2])
        await db_session.commit()

        # Set cleanup2 as primary
        response = await authenticated_client.put(
            f"/api/v1/cleaned-entries/{cleanup2.id}/set-primary"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(cleanup2.id)
        assert data["is_primary"] is True
        # Verify prompt template fields are included
        assert data["prompt_template_id"] == sample_prompt_template.id
        assert data["prompt_name"] == "Dream Analysis v1"
        assert data["prompt_description"] == "Standard dream analysis prompt"

        # Verify cleanup1 is no longer primary
        await db_session.refresh(cleanup1)
        assert cleanup1.is_primary is False

    @pytest.mark.asyncio
    async def test_set_primary_cleanup_not_completed(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test cannot set pending cleanup as primary."""
        from app.models.cleaned_entry import CleanedEntry, CleanupStatus
        import uuid

        # Create pending cleanup
        cleanup = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=None,
            model_name="llama3.2:3b",
            is_primary=False
        )
        cleanup.status = CleanupStatus.PENDING

        db_session.add(cleanup)
        await db_session.commit()

        # Try to set pending cleanup as primary
        response = await authenticated_client.put(
            f"/api/v1/cleaned-entries/{cleanup.id}/set-primary"
        )

        assert response.status_code == 400
        assert "must be completed" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_set_primary_cleanup_not_found(
        self,
        authenticated_client: AsyncClient
    ):
        """Test 404 for invalid cleanup ID."""
        import uuid

        fake_id = uuid.uuid4()
        response = await authenticated_client.put(
            f"/api/v1/cleaned-entries/{fake_id}/set-primary"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_cleanup_includes_is_primary(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that cleanup response includes is_primary field."""
        from app.models.cleaned_entry import CleanedEntry, CleanupStatus
        import uuid

        cleanup = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Test cleanup",
            model_name="llama3.2:3b",
            is_primary=True
        )
        cleanup.status = CleanupStatus.COMPLETED

        db_session.add(cleanup)
        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{cleanup.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert "is_primary" in data
        assert data["is_primary"] is True

    @pytest.mark.asyncio
    async def test_get_cleanup_without_prompt_template(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User,
        db_session: AsyncSession
    ):
        """Test that cleanup response handles missing prompt template gracefully."""
        from app.models.cleaned_entry import CleanedEntry, CleanupStatus
        import uuid

        # Create cleanup without prompt_template_id
        cleanup = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Test cleanup without prompt",
            model_name="llama3.2:3b",
            prompt_template_id=None,  # No prompt template
            is_primary=True
        )
        cleanup.status = CleanupStatus.COMPLETED

        db_session.add(cleanup)
        await db_session.commit()

        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{cleanup.id}"
        )

        assert response.status_code == 200
        data = response.json()
        # Verify prompt fields are None when no template
        assert data["prompt_template_id"] is None
        assert data["prompt_name"] is None
        assert data["prompt_description"] is None


# ============================================================================
# Parameter Tests (temperature, top_p)
# ============================================================================

class TestCleanupParameterHandling:
    """Test cleanup parameter handling (temperature, top_p)."""

    @pytest.mark.asyncio
    async def test_trigger_cleanup_with_temperature(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup accepts temperature parameter."""
        # Trigger cleanup with temperature
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"temperature": 0.7}
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_trigger_cleanup_with_top_p(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup accepts top_p parameter."""
        # Trigger cleanup with top_p
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"top_p": 0.9}
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_trigger_cleanup_with_both_parameters(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup accepts both temperature and top_p."""
        # Trigger cleanup with both parameters
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"temperature": 0.5, "top_p": 0.8}
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_trigger_cleanup_temperature_out_of_range_high(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup rejects temperature above 2.0."""
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"temperature": 3.0}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_trigger_cleanup_temperature_out_of_range_low(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup rejects negative temperature."""
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"temperature": -1.0}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_trigger_cleanup_top_p_out_of_range(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup rejects top_p above 1.0."""
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={"top_p": 1.5}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_trigger_cleanup_parameters_in_response(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        completed_transcription: Transcription,
        test_user: User
    ):
        """Test GET endpoint returns temperature and top_p parameters."""
        import json as json_lib
        # Create cleaned entry with parameters
        cleaned_entry = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=completed_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Test cleaned text",
            analysis=json_lib.dumps({"themes": [], "emotions": [], "characters": [], "locations": []}).encode("utf-8"),
            model_name="test-model",
            temperature=0.6,
            top_p=0.85,
            status="completed"
        )

        db_session.add(cleaned_entry)
        await db_session.commit()

        # Get cleaned entry and verify parameters in response
        response = await authenticated_client.get(
            f"/api/v1/cleaned-entries/{cleaned_entry.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["temperature"] == 0.6
        assert data["top_p"] == 0.85

    @pytest.mark.asyncio
    async def test_trigger_cleanup_without_parameters_backward_compatible(
        self,
        authenticated_client: AsyncClient,
        completed_transcription: Transcription
    ):
        """Test cleanup works without temperature/top_p (backward compatibility)."""
        # Trigger cleanup without parameters (empty body)
        response = await authenticated_client.post(
            f"/api/v1/transcriptions/{completed_transcription.id}/cleanup",
            json={}
        )

        assert response.status_code == 202
        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"
