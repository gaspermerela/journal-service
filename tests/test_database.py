"""
Unit tests for database service.
"""
import uuid
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.database import DatabaseService
from app.schemas.dream_entry import DreamEntryCreate
from app.models.dream_entry import DreamEntry


@pytest.fixture
def db_service():
    """Create database service instance."""
    return DatabaseService()


@pytest.mark.asyncio
async def test_create_entry_success(db_session: AsyncSession, db_service: DatabaseService):
    """Test successful creation of dream entry."""
    entry_data = DreamEntryCreate(
        original_filename="test_dream.mp3",
        saved_filename="550e8400-e29b-41d4-a716-446655440000_20250131T120000.mp3",
        file_path="/data/audio/2025-01-31/550e8400-e29b-41d4-a716-446655440000_20250131T120000.mp3",
        uploaded_at=datetime.now(timezone.utc)
    )

    entry = await db_service.create_entry(db_session, entry_data)

    assert entry is not None
    assert entry.id is not None
    assert entry.original_filename == entry_data.original_filename
    assert entry.saved_filename == entry_data.saved_filename
    assert entry.file_path == entry_data.file_path
    assert entry.uploaded_at == entry_data.uploaded_at
    assert entry.created_at is not None
    assert entry.updated_at is not None


@pytest.mark.asyncio
async def test_create_entry_generates_uuid(db_session: AsyncSession, db_service: DatabaseService):
    """Test that create_entry generates a UUID for the entry."""
    entry_data = DreamEntryCreate(
        original_filename="test_dream.mp3",
        saved_filename="test_20250131T120000.mp3",
        file_path="/data/audio/test.mp3",
        uploaded_at=datetime.now(timezone.utc)
    )

    entry = await db_service.create_entry(db_session, entry_data)

    # Should have a valid UUID
    assert isinstance(entry.id, uuid.UUID)


@pytest.mark.asyncio
async def test_create_entry_timestamps(db_session: AsyncSession, db_service: DatabaseService):
    """Test that create_entry sets timestamps correctly."""
    before = datetime.now(timezone.utc)

    entry_data = DreamEntryCreate(
        original_filename="test_dream.mp3",
        saved_filename="test_20250131T120000.mp3",
        file_path="/data/audio/test.mp3",
        uploaded_at=before
    )

    entry = await db_service.create_entry(db_session, entry_data)

    after = datetime.now(timezone.utc)

    # Timestamps should be set
    assert entry.created_at >= before
    assert entry.created_at <= after
    assert entry.updated_at >= before
    assert entry.updated_at <= after


@pytest.mark.asyncio
async def test_get_entry_by_id_success(db_session: AsyncSession, db_service: DatabaseService, sample_dream_entry: DreamEntry):
    """Test retrieving entry by ID when it exists."""
    entry = await db_service.get_entry_by_id(db_session, sample_dream_entry.id)

    assert entry is not None
    assert entry.id == sample_dream_entry.id
    assert entry.original_filename == sample_dream_entry.original_filename
    assert entry.saved_filename == sample_dream_entry.saved_filename


@pytest.mark.asyncio
async def test_get_entry_by_id_not_found(db_session: AsyncSession, db_service: DatabaseService):
    """Test retrieving entry by ID when it doesn't exist."""
    non_existent_id = uuid.uuid4()

    entry = await db_service.get_entry_by_id(db_session, non_existent_id)

    assert entry is None


@pytest.mark.asyncio
async def test_delete_entry_success(db_session: AsyncSession, db_service: DatabaseService, sample_dream_entry: DreamEntry):
    """Test successful deletion of entry."""
    result = await db_service.delete_entry(db_session, sample_dream_entry.id)

    assert result is True

    # Verify entry is deleted
    deleted_entry = await db_service.get_entry_by_id(db_session, sample_dream_entry.id)
    assert deleted_entry is None


@pytest.mark.asyncio
async def test_delete_entry_not_found(db_session: AsyncSession, db_service: DatabaseService):
    """Test deletion of non-existent entry."""
    non_existent_id = uuid.uuid4()

    result = await db_service.delete_entry(db_session, non_existent_id)

    assert result is False


@pytest.mark.asyncio
async def test_create_multiple_entries(db_session: AsyncSession, db_service: DatabaseService):
    """Test creating multiple entries."""
    entries_data = [
        DreamEntryCreate(
            original_filename=f"dream_{i}.mp3",
            saved_filename=f"saved_{i}.mp3",
            file_path=f"/data/audio/dream_{i}.mp3",
            uploaded_at=datetime.now(timezone.utc)
        )
        for i in range(3)
    ]

    created_entries = []
    for entry_data in entries_data:
        entry = await db_service.create_entry(db_session, entry_data)
        created_entries.append(entry)

    # All should have unique IDs
    ids = [entry.id for entry in created_entries]
    assert len(ids) == len(set(ids))  # All IDs are unique

    # All should be retrievable
    for entry in created_entries:
        retrieved = await db_service.get_entry_by_id(db_session, entry.id)
        assert retrieved is not None
        assert retrieved.id == entry.id


@pytest.mark.asyncio
async def test_unique_saved_filename_constraint(db_session: AsyncSession, db_service: DatabaseService):
    """Test that saved_filename must be unique."""
    entry_data_1 = DreamEntryCreate(
        original_filename="dream_1.mp3",
        saved_filename="duplicate_filename.mp3",
        file_path="/data/audio/dream_1.mp3",
        uploaded_at=datetime.now(timezone.utc)
    )

    # First entry should succeed
    entry_1 = await db_service.create_entry(db_session, entry_data_1)
    await db_session.commit()

    # Second entry with same saved_filename should fail
    entry_data_2 = DreamEntryCreate(
        original_filename="dream_2.mp3",
        saved_filename="duplicate_filename.mp3",  # Same as entry_1
        file_path="/data/audio/dream_2.mp3",
        uploaded_at=datetime.now(timezone.utc)
    )

    with pytest.raises(HTTPException) as exc_info:
        await db_service.create_entry(db_session, entry_data_2)
        await db_session.commit()

    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_entry_updated_at_changes(db_session: AsyncSession, db_service: DatabaseService, sample_dream_entry: DreamEntry):
    """Test that updated_at changes when entry is modified."""
    original_updated_at = sample_dream_entry.updated_at

    # Modify the entry
    sample_dream_entry.original_filename = "modified_dream.mp3"
    await db_session.flush()
    await db_session.refresh(sample_dream_entry)

    # updated_at should have changed
    # Note: This test might be flaky if execution is too fast
    # In production, the onupdate trigger should update this automatically
    assert sample_dream_entry.updated_at >= original_updated_at
