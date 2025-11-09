"""
Integration tests for entries endpoint.
"""
import uuid

import pytest
from httpx import AsyncClient

from app.models.voice_entry import VoiceEntry


@pytest.mark.asyncio
async def test_get_entry_by_id_success(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test retrieving an existing entry by ID."""
    response = await client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(sample_voice_entry.id)
    assert data["original_filename"] == sample_voice_entry.original_filename
    assert data["saved_filename"] == sample_voice_entry.saved_filename
    assert data["file_path"] == sample_voice_entry.file_path
    assert "uploaded_at" in data


@pytest.mark.asyncio
async def test_get_entry_by_id_not_found(client: AsyncClient):
    """Test retrieving a non-existent entry."""
    non_existent_id = uuid.uuid4()
    response = await client.get(f"/api/v1/entries/{non_existent_id}")

    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_entry_by_id_invalid_uuid(client: AsyncClient):
    """Test retrieving entry with invalid UUID format."""
    response = await client.get("/api/v1/entries/invalid-uuid")

    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_get_entry_response_format(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that entry response has correct format."""
    response = await client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Check all required fields are present
    required_fields = ["id", "original_filename", "saved_filename", "file_path", "uploaded_at"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(data["id"], str)
    assert isinstance(data["original_filename"], str)
    assert isinstance(data["saved_filename"], str)
    assert isinstance(data["file_path"], str)
    assert isinstance(data["uploaded_at"], str)


@pytest.mark.asyncio
async def test_get_entry_uuid_format(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that returned UUID is valid."""
    response = await client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Should be able to parse as UUID
    try:
        parsed_uuid = uuid.UUID(data["id"])
        assert parsed_uuid == sample_voice_entry.id
    except ValueError:
        pytest.fail("Invalid UUID format in response")


@pytest.mark.asyncio
async def test_get_entry_timestamp_format(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that timestamp is in ISO format."""
    response = await client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Should be ISO 8601 format
    from datetime import datetime
    try:
        datetime.fromisoformat(data["uploaded_at"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("Invalid timestamp format in response")


@pytest.mark.asyncio
async def test_get_multiple_entries(client: AsyncClient, db_session):
    """Test retrieving multiple different entries."""
    from app.services.database import DatabaseService
    from app.schemas.voice_entry import VoiceEntryCreate
    from datetime import datetime, timezone

    db_service = DatabaseService()

    # Create multiple entries
    entries = []
    for i in range(3):
        entry_data = VoiceEntryCreate(
            original_filename=f"dream_{i}.mp3",
            saved_filename=f"saved_{i}.mp3",
            file_path=f"/data/audio/dream_{i}.mp3",
            uploaded_at=datetime.now(timezone.utc)
        )
        entry = await db_service.create_entry(db_session, entry_data)
        await db_session.commit()
        entries.append(entry)

    # Retrieve each entry
    for entry in entries:
        response = await client.get(f"/api/v1/entries/{entry.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(entry.id)
        assert data["original_filename"] == entry.original_filename


@pytest.mark.asyncio
async def test_get_entry_after_upload(client: AsyncClient, sample_mp3_path):
    """Test retrieving an entry after uploading a file."""
    # First upload a file
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    entry_id = upload_data["id"]

    # Now retrieve the entry
    get_response = await client.get(f"/api/v1/entries/{entry_id}")

    assert get_response.status_code == 200
    get_data = get_response.json()

    # Data should match upload response
    assert get_data["id"] == upload_data["id"]
    assert get_data["original_filename"] == upload_data["original_filename"]
    assert get_data["saved_filename"] == upload_data["saved_filename"]
    assert get_data["file_path"] == upload_data["file_path"]
