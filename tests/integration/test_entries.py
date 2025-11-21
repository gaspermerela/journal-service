"""
Integration tests for entries endpoint.
Requires authentication.
"""
import uuid

import pytest
from httpx import AsyncClient

from app.models.voice_entry import VoiceEntry


@pytest.mark.asyncio
async def test_get_entry_by_id_success(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test retrieving an existing entry by ID."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == str(sample_voice_entry.id)
    assert data["original_filename"] == sample_voice_entry.original_filename
    assert data["saved_filename"] == sample_voice_entry.saved_filename
    assert "uploaded_at" in data


@pytest.mark.asyncio
async def test_get_entry_by_id_not_found(authenticated_client: AsyncClient):
    """Test retrieving a non-existent entry."""
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/api/v1/entries/{non_existent_id}")

    assert response.status_code == 404

    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_entry_by_id_invalid_uuid(authenticated_client: AsyncClient):
    """Test retrieving entry with invalid UUID format."""
    response = await authenticated_client.get("/api/v1/entries/invalid-uuid")

    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_get_entry_response_format(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that entry response has correct format."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Check all required fields are present
    required_fields = ["id", "original_filename", "saved_filename", "duration_seconds", "uploaded_at"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(data["id"], str)
    assert isinstance(data["original_filename"], str)
    assert isinstance(data["saved_filename"], str)
    assert isinstance(data["duration_seconds"], (int, float))
    assert isinstance(data["uploaded_at"], str)


@pytest.mark.asyncio
async def test_get_entry_uuid_format(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that returned UUID is valid."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Should be able to parse as UUID
    try:
        parsed_uuid = uuid.UUID(data["id"])
        assert parsed_uuid == sample_voice_entry.id
    except ValueError:
        pytest.fail("Invalid UUID format in response")


@pytest.mark.asyncio
async def test_get_entry_timestamp_format(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that timestamp is in ISO format."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")

    assert response.status_code == 200

    data = response.json()

    # Should be ISO 8601 format
    from datetime import datetime
    try:
        datetime.fromisoformat(data["uploaded_at"].replace("Z", "+00:00"))
    except ValueError:
        pytest.fail("Invalid timestamp format in response")


@pytest.mark.asyncio
async def test_get_multiple_entries(authenticated_client: AsyncClient, db_session, test_user):
    """Test retrieving multiple different entries."""
    from app.models.voice_entry import VoiceEntry
    import uuid

    # Create multiple entries
    entries = []
    for i in range(3):
        entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"dream_{i}.mp3",
            saved_filename=f"saved_{i}.mp3",
            file_path=f"/data/audio/dream_{i}.mp3",
            user_id=test_user.id
        )
        db_session.add(entry)
        await db_session.commit()
        await db_session.refresh(entry)
        entries.append(entry)

    # Retrieve each entry
    for entry in entries:
        response = await authenticated_client.get(f"/api/v1/entries/{entry.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == str(entry.id)
        assert data["original_filename"] == entry.original_filename


@pytest.mark.asyncio
async def test_get_entry_after_upload(authenticated_client: AsyncClient, sample_mp3_path):
    """Test retrieving an entry after uploading a file."""
    # First upload a file
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test.mp3", f, "audio/mpeg")}
        upload_response = await authenticated_client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    entry_id = upload_data["id"]

    # Now retrieve the entry
    get_response = await authenticated_client.get(f"/api/v1/entries/{entry_id}")

    assert get_response.status_code == 200
    get_data = get_response.json()

    # Data should match upload response
    assert get_data["id"] == upload_data["id"]
    assert get_data["original_filename"] == upload_data["original_filename"]
    assert get_data["saved_filename"] == upload_data["saved_filename"]


# ===== List Entries Tests =====

@pytest.mark.asyncio
async def test_list_entries_empty(authenticated_client: AsyncClient):
    """Test listing entries when user has no entries."""
    response = await authenticated_client.get("/api/v1/entries")

    assert response.status_code == 200

    data = response.json()
    assert data["entries"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_list_entries_basic(authenticated_client: AsyncClient, db_session, test_user):
    """Test listing entries with basic data."""
    from app.models.voice_entry import VoiceEntry

    # Create 3 entries
    entries = []
    for i in range(3):
        entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"dream_{i}.mp3",
            saved_filename=f"saved_{i}.mp3",
            file_path=f"/data/audio/dream_{i}.mp3",
            entry_type="dream",
            duration_seconds=60.5 + i,
            user_id=test_user.id
        )
        db_session.add(entry)
        entries.append(entry)

    await db_session.commit()

    # List entries
    response = await authenticated_client.get("/api/v1/entries")

    assert response.status_code == 200

    data = response.json()
    assert len(data["entries"]) == 3
    assert data["total"] == 3
    assert data["limit"] == 20
    assert data["offset"] == 0

    # Check first entry has required fields
    entry = data["entries"][0]
    assert "id" in entry
    assert "original_filename" in entry
    assert "saved_filename" in entry
    assert "entry_type" in entry
    assert "duration_seconds" in entry
    assert "uploaded_at" in entry


@pytest.mark.asyncio
async def test_list_entries_ordering(authenticated_client: AsyncClient, db_session, test_user):
    """Test that entries are ordered by uploaded_at DESC (newest first)."""
    from app.models.voice_entry import VoiceEntry
    from datetime import datetime, timezone, timedelta

    # Create entries with different timestamps
    now = datetime.now(timezone.utc)
    entries_data = [
        ("oldest.mp3", now - timedelta(hours=2)),
        ("middle.mp3", now - timedelta(hours=1)),
        ("newest.mp3", now)
    ]

    for filename, timestamp in entries_data:
        entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=filename,
            saved_filename=filename,
            file_path=f"/data/audio/{filename}",
            entry_type="dream",
            duration_seconds=60.0,
            uploaded_at=timestamp,
            user_id=test_user.id
        )
        db_session.add(entry)

    await db_session.commit()

    # List entries
    response = await authenticated_client.get("/api/v1/entries")

    assert response.status_code == 200

    data = response.json()
    assert len(data["entries"]) == 3

    # Should be ordered newest to oldest
    assert data["entries"][0]["original_filename"] == "newest.mp3"
    assert data["entries"][1]["original_filename"] == "middle.mp3"
    assert data["entries"][2]["original_filename"] == "oldest.mp3"


@pytest.mark.asyncio
async def test_list_entries_pagination(authenticated_client: AsyncClient, db_session, test_user):
    """Test pagination with limit and offset."""
    from app.models.voice_entry import VoiceEntry

    # Create 10 entries
    for i in range(10):
        entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"entry_{i:02d}.mp3",
            saved_filename=f"saved_{i:02d}.mp3",
            file_path=f"/data/audio/entry_{i:02d}.mp3",
            entry_type="dream",
            duration_seconds=60.0,
            user_id=test_user.id
        )
        db_session.add(entry)

    await db_session.commit()

    # Get first page (limit=3, offset=0)
    response1 = await authenticated_client.get("/api/v1/entries?limit=3&offset=0")
    assert response1.status_code == 200
    data1 = response1.json()
    assert len(data1["entries"]) == 3
    assert data1["total"] == 10
    assert data1["limit"] == 3
    assert data1["offset"] == 0

    # Get second page (limit=3, offset=3)
    response2 = await authenticated_client.get("/api/v1/entries?limit=3&offset=3")
    assert response2.status_code == 200
    data2 = response2.json()
    assert len(data2["entries"]) == 3
    assert data2["total"] == 10
    assert data2["limit"] == 3
    assert data2["offset"] == 3

    # Entries should be different
    ids1 = {e["id"] for e in data1["entries"]}
    ids2 = {e["id"] for e in data2["entries"]}
    assert ids1.isdisjoint(ids2)


@pytest.mark.asyncio
async def test_list_entries_filter_by_type(authenticated_client: AsyncClient, db_session, test_user):
    """Test filtering entries by entry_type."""
    from app.models.voice_entry import VoiceEntry

    # Create entries with different types
    types = ["dream", "dream", "journal", "note"]
    for i, entry_type in enumerate(types):
        entry = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"{entry_type}_{i}.mp3",
            saved_filename=f"saved_{i}.mp3",
            file_path=f"/data/audio/{entry_type}_{i}.mp3",
            entry_type=entry_type,
            duration_seconds=60.0,
            user_id=test_user.id
        )
        db_session.add(entry)

    await db_session.commit()

    # Filter for dreams only
    response = await authenticated_client.get("/api/v1/entries?entry_type=dream")
    assert response.status_code == 200

    data = response.json()
    assert len(data["entries"]) == 2
    assert data["total"] == 2
    assert all(e["entry_type"] == "dream" for e in data["entries"])


@pytest.mark.asyncio
async def test_list_entries_limit_validation(authenticated_client: AsyncClient):
    """Test that limit is validated (1-100)."""
    # Too small
    response1 = await authenticated_client.get("/api/v1/entries?limit=0")
    assert response1.status_code == 422

    # Too large
    response2 = await authenticated_client.get("/api/v1/entries?limit=101")
    assert response2.status_code == 422

    # Valid
    response3 = await authenticated_client.get("/api/v1/entries?limit=50")
    assert response3.status_code == 200


@pytest.mark.asyncio
async def test_list_entries_offset_validation(authenticated_client: AsyncClient):
    """Test that offset is validated (>= 0)."""
    # Negative offset
    response1 = await authenticated_client.get("/api/v1/entries?offset=-1")
    assert response1.status_code == 422

    # Valid
    response2 = await authenticated_client.get("/api/v1/entries?offset=0")
    assert response2.status_code == 200


@pytest.mark.asyncio
async def test_get_entry_duration_included(authenticated_client: AsyncClient, db_session, test_user):
    """Test that duration_seconds is included in single entry response."""
    from app.models.voice_entry import VoiceEntry

    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="test.mp3",
        saved_filename="saved.mp3",
        file_path="/data/audio/test.mp3",
        entry_type="dream",
        duration_seconds=123.45,
        user_id=test_user.id
    )
    db_session.add(entry)
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/entries/{entry.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["duration_seconds"] == 123.45


@pytest.mark.asyncio
async def test_list_entries_duration_included(authenticated_client: AsyncClient, db_session, test_user):
    """Test that duration_seconds is included in list response."""
    from app.models.voice_entry import VoiceEntry

    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="test.mp3",
        saved_filename="saved.mp3",
        file_path="/data/audio/test.mp3",
        entry_type="dream",
        duration_seconds=123.45,
        user_id=test_user.id
    )
    db_session.add(entry)
    await db_session.commit()

    response = await authenticated_client.get("/api/v1/entries")
    assert response.status_code == 200

    data = response.json()
    assert len(data["entries"]) == 1
    assert data["entries"][0]["duration_seconds"] == 123.45


@pytest.mark.asyncio
async def test_list_entries_user_isolation(authenticated_client: AsyncClient, db_session, test_user):
    """Test that users only see their own entries."""
    from app.models.voice_entry import VoiceEntry
    from app.models.user import User
    from app.utils.security import hash_password

    # Create another user
    other_user = User(
        id=uuid.uuid4(),
        email="other@example.com",
        hashed_password=hash_password("password123")
    )
    db_session.add(other_user)
    await db_session.commit()

    # Create entries for both users
    for i in range(2):
        entry1 = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"user1_{i}.mp3",
            saved_filename=f"user1_saved_{i}.mp3",
            file_path=f"/data/audio/user1_{i}.mp3",
            entry_type="dream",
            duration_seconds=60.0,
            user_id=test_user.id
        )
        entry2 = VoiceEntry(
            id=uuid.uuid4(),
            original_filename=f"user2_{i}.mp3",
            saved_filename=f"user2_saved_{i}.mp3",
            file_path=f"/data/audio/user2_{i}.mp3",
            entry_type="dream",
            duration_seconds=60.0,
            user_id=other_user.id
        )
        db_session.add(entry1)
        db_session.add(entry2)

    await db_session.commit()

    # authenticated_client is authenticated as test_user
    response = await authenticated_client.get("/api/v1/entries")
    assert response.status_code == 200

    data = response.json()
    # Should only see test_user's 2 entries, not other_user's 2 entries
    assert len(data["entries"]) == 2
    assert data["total"] == 2
    assert all("user1_" in e["original_filename"] for e in data["entries"])
