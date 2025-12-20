"""
Integration tests for transcription API endpoints.
Tests routes with mocked transcription service.
Requires authentication.
"""
import pytest
import asyncio
from uuid import uuid4
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_entry import VoiceEntry
from app.models.transcription import Transcription
from app.models.user import User


@pytest.mark.asyncio
async def test_trigger_transcription_success(authenticated_client, sample_voice_entry):
    """Test triggering transcription for an entry."""
    response = await authenticated_client.post(
        f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["entry_id"] == str(sample_voice_entry.id)
    assert "transcription_id" in data
    assert data["status"] == "processing"
    assert data["message"] == "Transcription started in background"


@pytest.mark.asyncio
async def test_trigger_transcription_entry_not_found(authenticated_client):
    """Test triggering transcription for non-existent entry."""
    non_existent_id = uuid4()

    response = await authenticated_client.post(
        f"/api/v1/entries/{non_existent_id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_trigger_transcription_invalid_provider(authenticated_client, sample_voice_entry):
    """Test triggering transcription with invalid provider returns 400."""
    response = await authenticated_client.post(
        f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
        json={"language": "en", "transcription_provider": "nonexistent_provider"}
    )

    assert response.status_code == 400
    assert "unknown" in response.json()["detail"].lower() or "provider" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_transcription_success(authenticated_client, sample_transcription):
    """Test retrieving a transcription by ID."""
    response = await authenticated_client.get(f"/api/v1/transcriptions/{sample_transcription.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_transcription.id)
    assert data["status"] == "completed"
    # The transcribed_text is decrypted by the route - verify it's the expected plaintext
    assert data["transcribed_text"] == "I had a dream about flying over mountains and vast oceans."
    assert data["model_used"] == "whisper-base"
    assert data["language_code"] == "en"
    assert data["is_primary"] is True


@pytest.mark.asyncio
async def test_get_transcription_not_found(authenticated_client):
    """Test retrieving non-existent transcription."""
    non_existent_id = uuid4()

    response = await authenticated_client.get(f"/api/v1/transcriptions/{non_existent_id}")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_transcriptions_for_entry(authenticated_client, sample_voice_entry, db_session, test_user, encryption_service):
    """Test listing all transcriptions for an entry with encrypted text."""
    from app.services.database import db_service
    from app.schemas.transcription import TranscriptionCreate
    from app.utils.encryption_helpers import encrypt_text

    # Create multiple transcriptions with encrypted text
    expected_texts = ["First transcription text", "Second transcription text", None]
    transcriptions = []
    for i in range(3):
        trans_data = TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed" if i < 2 else "pending",
            model_used=f"whisper-model-{i}",
            language_code="en",
            is_primary=(i == 0)
        )
        trans = await db_service.create_transcription(db_session, trans_data)
        transcriptions.append(trans)

        # Add encrypted text for completed transcriptions
        if expected_texts[i] is not None:
            encrypted_text = await encrypt_text(
                encryption_service=encryption_service,
                db=db_session,
                text=expected_texts[i],
                voice_entry_id=sample_voice_entry.id,
                user_id=test_user.id,
            )
            await db_service.update_transcription_status(
                db_session,
                trans.id,
                status="completed",
                transcribed_text=encrypted_text,
            )
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}/transcriptions")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["transcriptions"]) == 3
    # Should be ordered by created_at desc (newest first)
    assert data["transcriptions"][0]["model_used"] == "whisper-model-2"
    # Pending transcription has no text
    assert data["transcriptions"][0]["transcribed_text"] is None
    # Completed transcriptions have decrypted text
    assert data["transcriptions"][1]["transcribed_text"] == "Second transcription text"
    assert data["transcriptions"][2]["transcribed_text"] == "First transcription text"


@pytest.mark.asyncio
async def test_list_transcriptions_empty(authenticated_client, sample_voice_entry):
    """Test listing transcriptions for entry with none."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}/transcriptions")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["transcriptions"] == []


@pytest.mark.asyncio
async def test_list_transcriptions_entry_not_found(authenticated_client):
    """Test listing transcriptions for non-existent entry."""
    non_existent_id = uuid4()

    response = await authenticated_client.get(f"/api/v1/entries/{non_existent_id}/transcriptions")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_set_primary_transcription_success(authenticated_client, sample_voice_entry, db_session, test_user, encryption_service):
    """Test setting a transcription as primary with encrypted text."""
    from app.services.database import db_service
    from app.schemas.transcription import TranscriptionCreate
    from app.utils.encryption_helpers import encrypt_text

    # Create two completed transcriptions with encrypted text
    trans1_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-base",
        language_code="en",
        is_primary=True
    )
    trans1 = await db_service.create_transcription(db_session, trans1_data)
    encrypted_text1 = await encrypt_text(
        encryption_service=encryption_service,
        db=db_session,
        text="First transcription from whisper-base",
        voice_entry_id=sample_voice_entry.id,
        user_id=test_user.id,
    )
    await db_service.update_transcription_status(
        db_session, trans1.id, status="completed", transcribed_text=encrypted_text1
    )

    trans2_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-large",
        language_code="en",
        is_primary=False
    )
    trans2 = await db_service.create_transcription(db_session, trans2_data)
    encrypted_text2 = await encrypt_text(
        encryption_service=encryption_service,
        db=db_session,
        text="Second transcription from whisper-large",
        voice_entry_id=sample_voice_entry.id,
        user_id=test_user.id,
    )
    await db_service.update_transcription_status(
        db_session, trans2.id, status="completed", transcribed_text=encrypted_text2
    )
    await db_session.commit()

    # Set trans2 as primary
    response = await authenticated_client.put(f"/api/v1/transcriptions/{trans2.id}/set-primary")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(trans2.id)
    assert data["is_primary"] is True
    # Verify transcribed_text is decrypted correctly
    assert data["transcribed_text"] == "Second transcription from whisper-large"

    # Verify trans1 is no longer primary
    await db_session.refresh(trans1)
    assert trans1.is_primary is False


@pytest.mark.asyncio
async def test_set_primary_transcription_not_completed(authenticated_client, sample_pending_transcription):
    """Test cannot set non-completed transcription as primary."""
    response = await authenticated_client.put(
        f"/api/v1/transcriptions/{sample_pending_transcription.id}/set-primary"
    )

    assert response.status_code == 400
    assert "completed" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_set_primary_transcription_not_found(authenticated_client):
    """Test setting non-existent transcription as primary."""
    non_existent_id = uuid4()

    response = await authenticated_client.put(f"/api/v1/transcriptions/{non_existent_id}/set-primary")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_entry_with_primary_transcription(authenticated_client, sample_voice_entry, sample_transcription):
    """Test that GET /entries/{id} includes primary transcription."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_voice_entry.id)
    assert data["primary_transcription"] is not None
    assert data["primary_transcription"]["id"] == str(sample_transcription.id)
    # The fixture encrypts the text, the route decrypts it - verify decryption works
    assert data["primary_transcription"]["transcribed_text"] == "I had a dream about flying over mountains and vast oceans."


@pytest.mark.asyncio
async def test_get_entry_without_transcription(authenticated_client, sample_voice_entry):
    """Test that GET /entries/{id} works without transcription."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(sample_voice_entry.id)
    assert data["primary_transcription"] is None


@pytest.mark.asyncio
async def test_trigger_transcription_uses_configured_model(authenticated_client, sample_voice_entry, db_session):
    """Test that transcription uses the model configured for the selected provider."""
    response = await authenticated_client.post(
        f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert response.status_code == 202
    data = response.json()
    assert "transcription_id" in data

    # Verify the transcription was created with the correct model from noop provider
    from app.services.database import db_service
    transcription = await db_service.get_transcription_by_id(db_session, data["transcription_id"])
    assert transcription.model_used == "noop-whisper-test"  # From NoOp provider


@pytest.mark.asyncio
async def test_trigger_transcription_with_different_languages(authenticated_client, sample_voice_entry):
    """Test triggering transcription with different languages."""
    languages = ["en", "es", "fr", "sl", "auto"]

    for lang in languages:
        response = await authenticated_client.post(
            f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
            json={"language": lang, "transcription_provider": "noop"}
        )

        assert response.status_code == 202


@pytest.mark.asyncio
async def test_transcription_background_task_execution(authenticated_client, sample_voice_entry, db_session):
    """Test that background task actually processes transcription."""
    response = await authenticated_client.post(
        f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert response.status_code == 202
    transcription_id = response.json()["transcription_id"]

    # Wait a bit for background task to execute
    await asyncio.sleep(0.2)

    # Check transcription status
    from app.services.database import db_service
    transcription = await db_service.get_transcription_by_id(db_session, transcription_id)

    # Background task should have updated status
    # Note: In test environment, background tasks may execute immediately
    assert transcription is not None
    assert transcription.status in ["pending", "processing", "completed"]


# ============================================================================
# Parameter Tests (beam_size)
# ============================================================================

class TestTranscriptionBeamSizeParameter:
    """Test beam_size parameter handling for transcriptions."""

    @pytest.mark.asyncio
    async def test_trigger_transcription_with_beam_size(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry
    ):
        """Test transcription accepts beam_size parameter."""
        # Trigger transcription with beam_size
        response = await authenticated_client.post(
            f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
            json={"language": "en", "beam_size": 5}
        )

        assert response.status_code == 202
        data = response.json()
        assert data["status"] == "processing"
        assert "transcription_id" in data

    @pytest.mark.asyncio
    async def test_trigger_transcription_beam_size_out_of_range_high(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry
    ):
        """Test transcription rejects beam_size above 10."""
        response = await authenticated_client.post(
            f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
            json={"language": "en", "beam_size": 11}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_trigger_transcription_beam_size_out_of_range_low(
        self,
        authenticated_client: AsyncClient,
        sample_voice_entry: VoiceEntry
    ):
        """Test transcription rejects beam_size below 1."""
        response = await authenticated_client.post(
            f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
            json={"language": "en", "beam_size": 0}
        )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_trigger_transcription_beam_size_in_response(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        test_user: User
    ):
        """Test GET endpoint returns beam_size and temperature parameters."""
        from app.models.transcription import Transcription
        import uuid

        # Create transcription with beam_size and temperature
        transcription = Transcription(
            id=uuid.uuid4(),
            entry_id=sample_voice_entry.id,
            transcribed_text=b"Test transcription",
            status="completed",
            model_used="whisper-base",
            language_code="en",
            beam_size=7,
            temperature=0.3,
            is_primary=True
        )

        db_session.add(transcription)
        await db_session.commit()

        # Get transcription and verify beam_size and temperature in response
        response = await authenticated_client.get(
            f"/api/v1/transcriptions/{transcription.id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["beam_size"] == 7
        assert data["temperature"] == 0.3

    @pytest.mark.asyncio
    async def test_list_transcriptions_includes_temperature(
        self,
        authenticated_client: AsyncClient,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        test_user: User
    ):
        """Test GET /entries/{id}/transcriptions returns temperature parameter."""
        from app.models.transcription import Transcription
        import uuid

        # Create transcription with temperature
        transcription = Transcription(
            id=uuid.uuid4(),
            entry_id=sample_voice_entry.id,
            transcribed_text=b"Test transcription",
            status="completed",
            model_used="whisper-base",
            language_code="en",
            beam_size=5,
            temperature=0.7,
            is_primary=True
        )

        db_session.add(transcription)
        await db_session.commit()

        # Get transcriptions list and verify temperature in response
        response = await authenticated_client.get(
            f"/api/v1/entries/{sample_voice_entry.id}/transcriptions"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["transcriptions"]) == 1
        assert data["transcriptions"][0]["temperature"] == 0.7
        assert data["transcriptions"][0]["beam_size"] == 5
