"""
Integration tests for transcription database operations.
Tests DatabaseService transcription CRUD methods.
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone

from app.services.database import db_service
from app.schemas.transcription import TranscriptionCreate
from app.models.transcription import Transcription


@pytest.mark.asyncio
async def test_create_transcription(db_session, sample_voice_entry):
    """Test creating a new transcription record."""
    transcription_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="pending",
        model_used="whisper-base",
        language_code="en",
        is_primary=False
    )

    transcription = await db_service.create_transcription(db_session, transcription_data)
    await db_session.commit()

    assert transcription.id is not None
    assert transcription.entry_id == sample_voice_entry.id
    assert transcription.status == "pending"
    assert transcription.model_used == "whisper-base"
    assert transcription.language_code == "en"
    assert transcription.is_primary is False
    assert transcription.transcribed_text is None


@pytest.mark.asyncio
async def test_get_transcription_by_id(db_session, sample_transcription):
    """Test retrieving a transcription by ID."""
    transcription = await db_service.get_transcription_by_id(
        db_session,
        sample_transcription.id
    )

    assert transcription is not None
    assert transcription.id == sample_transcription.id
    assert transcription.transcribed_text == sample_transcription.transcribed_text


@pytest.mark.asyncio
async def test_get_transcription_by_id_not_found(db_session):
    """Test retrieving non-existent transcription returns None."""
    non_existent_id = uuid4()

    transcription = await db_service.get_transcription_by_id(db_session, non_existent_id)

    assert transcription is None


@pytest.mark.asyncio
async def test_get_transcriptions_for_entry(db_session, sample_voice_entry):
    """Test retrieving all transcriptions for an entry."""
    # Create multiple transcriptions for the same entry
    for i in range(3):
        transcription_data = TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed" if i == 0 else "pending",
            model_used=f"whisper-base-{i}",
            language_code="en",
            is_primary=(i == 0)
        )
        await db_service.create_transcription(db_session, transcription_data)

    await db_session.commit()

    transcriptions = await db_service.get_transcriptions_for_entry(
        db_session,
        sample_voice_entry.id
    )

    assert len(transcriptions) == 3
    # Should be ordered by created_at desc (newest first)
    assert transcriptions[0].model_used == "whisper-base-2"


@pytest.mark.asyncio
async def test_get_transcriptions_for_entry_empty(db_session, sample_voice_entry):
    """Test getting transcriptions for entry with no transcriptions."""
    transcriptions = await db_service.get_transcriptions_for_entry(
        db_session,
        sample_voice_entry.id
    )

    assert transcriptions == []


@pytest.mark.asyncio
async def test_get_primary_transcription(db_session, sample_voice_entry):
    """Test retrieving the primary transcription for an entry."""
    # Create non-primary transcription
    transcription_data_1 = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-tiny",
        language_code="en",
        is_primary=False
    )
    await db_service.create_transcription(db_session, transcription_data_1)

    # Create primary transcription
    transcription_data_2 = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-large",
        language_code="en",
        is_primary=True
    )
    primary = await db_service.create_transcription(db_session, transcription_data_2)
    await db_session.commit()

    result = await db_service.get_primary_transcription(db_session, sample_voice_entry.id)

    assert result is not None
    assert result.id == primary.id
    assert result.is_primary is True
    assert result.model_used == "whisper-large"


@pytest.mark.asyncio
async def test_get_primary_transcription_none(db_session, sample_voice_entry):
    """Test getting primary transcription when none exists."""
    result = await db_service.get_primary_transcription(db_session, sample_voice_entry.id)

    assert result is None


@pytest.mark.asyncio
async def test_update_transcription_status_to_processing(db_session, sample_pending_transcription):
    """Test updating transcription status from pending to processing."""
    updated = await db_service.update_transcription_status(
        db_session,
        sample_pending_transcription.id,
        status="processing"
    )
    await db_session.commit()

    assert updated is not None
    assert updated.status == "processing"
    assert updated.transcription_started_at is not None
    assert updated.transcription_completed_at is None


@pytest.mark.asyncio
async def test_update_transcription_status_to_completed(db_session, sample_pending_transcription):
    """Test updating transcription status to completed with text."""
    transcribed_text = "This is the transcribed text from the audio."

    updated = await db_service.update_transcription_status(
        db_session,
        sample_pending_transcription.id,
        status="completed",
        transcribed_text=transcribed_text
    )
    await db_session.commit()

    assert updated is not None
    assert updated.status == "completed"
    assert updated.transcribed_text == transcribed_text
    assert updated.transcription_completed_at is not None


@pytest.mark.asyncio
async def test_update_transcription_status_to_failed(db_session, sample_pending_transcription):
    """Test updating transcription status to failed with error message."""
    error_message = "Model failed to transcribe audio"

    updated = await db_service.update_transcription_status(
        db_session,
        sample_pending_transcription.id,
        status="failed",
        error_message=error_message
    )
    await db_session.commit()

    assert updated is not None
    assert updated.status == "failed"
    assert updated.error_message == error_message
    assert updated.transcription_completed_at is not None


@pytest.mark.asyncio
async def test_update_transcription_status_not_found(db_session):
    """Test updating non-existent transcription returns None."""
    non_existent_id = uuid4()

    updated = await db_service.update_transcription_status(
        db_session,
        non_existent_id,
        status="completed"
    )

    assert updated is None


@pytest.mark.asyncio
async def test_set_primary_transcription(db_session, sample_voice_entry):
    """Test setting a transcription as primary."""
    # Create two transcriptions
    trans1_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-base",
        language_code="en",
        is_primary=True  # Initially primary
    )
    trans1 = await db_service.create_transcription(db_session, trans1_data)

    trans2_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-large",
        language_code="en",
        is_primary=False
    )
    trans2 = await db_service.create_transcription(db_session, trans2_data)
    await db_session.commit()

    # Set trans2 as primary
    updated = await db_service.set_primary_transcription(db_session, trans2.id)
    await db_session.commit()

    # Refresh both transcriptions
    await db_session.refresh(trans1)
    await db_session.refresh(trans2)

    assert updated is not None
    assert updated.id == trans2.id
    assert trans2.is_primary is True
    assert trans1.is_primary is False  # Should be unset


@pytest.mark.asyncio
async def test_set_primary_transcription_not_found(db_session):
    """Test setting non-existent transcription as primary returns None."""
    non_existent_id = uuid4()

    result = await db_service.set_primary_transcription(db_session, non_existent_id)

    assert result is None


@pytest.mark.asyncio
async def test_set_primary_transcription_unsets_previous(db_session, sample_voice_entry):
    """Test that setting primary unsets any previous primary transcription."""
    # Create three transcriptions
    transcriptions = []
    for i in range(3):
        trans_data = TranscriptionCreate(
            entry_id=sample_voice_entry.id,
            status="completed",
            model_used=f"whisper-model-{i}",
            language_code="en",
            is_primary=(i == 0)  # First one is primary
        )
        trans = await db_service.create_transcription(db_session, trans_data)
        transcriptions.append(trans)

    await db_session.commit()

    # Set third as primary
    await db_service.set_primary_transcription(db_session, transcriptions[2].id)
    await db_session.commit()

    # Check all transcriptions
    for i, trans in enumerate(transcriptions):
        await db_session.refresh(trans)
        if i == 2:
            assert trans.is_primary is True
        else:
            assert trans.is_primary is False


@pytest.mark.asyncio
async def test_transcription_cascade_delete(db_session, sample_voice_entry):
    """Test that deleting an entry cascades to delete transcriptions."""
    # Create transcription for entry
    trans_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-base",
        language_code="en",
        is_primary=True
    )
    trans = await db_service.create_transcription(db_session, trans_data)
    await db_session.commit()
    trans_id = trans.id

    # Delete the entry
    await db_service.delete_entry(db_session, sample_voice_entry.id)
    await db_session.commit()

    # Try to retrieve transcription - should not exist
    result = await db_service.get_transcription_by_id(db_session, trans_id)
    assert result is None
