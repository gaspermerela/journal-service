"""
Integration tests for cleaned entry database operations with parameters.
"""
import pytest
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.cleaned_entry import CleanedEntry, CleanupStatus
from app.models.transcription import Transcription
from app.models.voice_entry import VoiceEntry
from app.models.user import User
from app.services.database import db_service


class TestCleanedEntryDatabaseParameters:
    """Test database operations for cleaned entries with temperature/top_p parameters."""

    @pytest.mark.asyncio
    async def test_create_cleaned_entry_with_temperature_top_p(
        self,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        sample_transcription: Transcription,
        test_user: User
    ):
        """Test creating cleaned entry with temperature and top_p parameters."""
        # Create cleaned entry with parameters
        # cleaned_text is LargeBinary (encrypted bytes)
        cleaned_entry = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=sample_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Test cleaned text",
            model_name="test-model",
            temperature=0.75,
            top_p=0.95,
            status="completed"
        )

        db_session.add(cleaned_entry)
        await db_session.commit()
        await db_session.refresh(cleaned_entry)

        # Verify parameters were stored
        assert cleaned_entry.temperature == 0.75
        assert cleaned_entry.top_p == 0.95

    @pytest.mark.asyncio
    async def test_update_cleaned_entry_parameters(
        self,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        sample_transcription: Transcription,
        test_user: User
    ):
        """Test that parameters are immutable - they cannot be changed via update_cleaned_entry_processing."""
        # Create initial cleaned entry WITH parameters set at creation
        cleaned_entry = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=sample_transcription.id,
            user_id=test_user.id,
            model_name="test-model",
            status="pending",
            temperature=0.5,  # Set at creation
            top_p=0.8        # Set at creation
        )

        db_session.add(cleaned_entry)
        await db_session.commit()

        # Try to update with different parameter values (should be ignored)
        # cleaned_text is LargeBinary (encrypted bytes)
        updated_entry = await db_service.update_cleaned_entry_processing(
            db=db_session,
            cleaned_entry_id=cleaned_entry.id,
            cleanup_status=CleanupStatus.COMPLETED,
            cleaned_text=b"Updated cleaned text",
            temperature=0.9,  # Should be IGNORED (immutable)
            top_p=0.95       # Should be IGNORED (immutable)
        )

        # Verify parameters UNCHANGED (immutable behavior)
        assert updated_entry.temperature == 0.5  # Original value
        assert updated_entry.top_p == 0.8        # Original value
        assert updated_entry.cleaned_text == b"Updated cleaned text"  # Other fields DO update

    @pytest.mark.asyncio
    async def test_query_cleaned_entries_with_parameters(
        self,
        db_session: AsyncSession,
        sample_voice_entry: VoiceEntry,
        sample_transcription: Transcription,
        test_user: User
    ):
        """Test querying cleaned entries and verifying parameters are retrieved."""
        # Create multiple cleaned entries with different parameters
        # cleaned_text is LargeBinary (encrypted bytes)
        entry1 = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=sample_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Entry 1",
            model_name="model-1",
            temperature=0.3,
            top_p=0.8,
            status="completed"
        )

        entry2 = CleanedEntry(
            id=uuid.uuid4(),
            voice_entry_id=sample_voice_entry.id,
            transcription_id=sample_transcription.id,
            user_id=test_user.id,
            cleaned_text=b"Entry 2",
            model_name="model-2",
            temperature=0.7,
            top_p=0.9,
            status="completed"
        )

        db_session.add_all([entry1, entry2])
        await db_session.commit()

        # Query cleaned entries
        entries = await db_service.get_cleaned_entries_by_voice_entry(
            db=db_session,
            voice_entry_id=sample_voice_entry.id,
            user_id=test_user.id
        )

        # Verify both entries retrieved with correct parameters
        assert len(entries) >= 2

        # Find our test entries
        test_entries = [e for e in entries if e.id in [entry1.id, entry2.id]]
        assert len(test_entries) == 2

        # Verify parameters
        for entry in test_entries:
            if entry.id == entry1.id:
                assert entry.temperature == 0.3
                assert entry.top_p == 0.8
            elif entry.id == entry2.id:
                assert entry.temperature == 0.7
                assert entry.top_p == 0.9
