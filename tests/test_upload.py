"""
Integration tests for upload endpoint.
"""
import io
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_valid_mp3(client: AsyncClient, sample_mp3_path: Path, test_storage_path: Path):
    """Test uploading a valid MP3 file."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream_recording.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert "original_filename" in data
    assert "saved_filename" in data
    assert "file_path" in data
    assert "uploaded_at" in data
    assert "message" in data

    # Verify data
    assert data["original_filename"] == "dream_recording.mp3"
    assert data["saved_filename"].endswith(".mp3")
    assert data["message"] == "File uploaded successfully"

    # Verify UUID format
    try:
        uuid.UUID(data["id"])
    except ValueError:
        pytest.fail("Invalid UUID format")

    # Verify file was saved
    file_path = Path(data["file_path"])
    assert file_path.exists()
    assert file_path.is_file()


@pytest.mark.asyncio
async def test_upload_no_file(client: AsyncClient):
    """Test upload endpoint with no file."""
    response = await client.post("/api/v1/upload")

    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_upload_invalid_file_type(client: AsyncClient, invalid_file_path: Path):
    """Test uploading a non-MP3 file."""
    with open(invalid_file_path, 'rb') as f:
        files = {"file": ("document.txt", f, "text/plain")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_file_too_large(client: AsyncClient, large_mp3_path: Path):
    """Test uploading a file that exceeds size limit."""
    with open(large_mp3_path, 'rb') as f:
        files = {"file": ("large_dream.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 413

    data = response.json()
    assert "detail" in data
    assert "too large" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_empty_file(client: AsyncClient):
    """Test uploading an empty file."""
    files = {"file": ("empty.mp3", io.BytesIO(b""), "audio/mpeg")}
    response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_creates_date_folder(client: AsyncClient, sample_mp3_path: Path, test_storage_path: Path):
    """Test that upload creates date-based folder structure."""
    from datetime import datetime, timezone

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    file_path = data["file_path"]

    # Verify date folder exists in path
    expected_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert expected_date in file_path


@pytest.mark.asyncio
async def test_upload_multiple_files(client: AsyncClient, sample_mp3_path: Path):
    """Test uploading multiple files creates separate entries."""
    file_ids = []

    for i in range(3):
        with open(sample_mp3_path, 'rb') as f:
            files = {"file": (f"dream_{i}.mp3", f, "audio/mpeg")}
            response = await client.post("/api/v1/upload", files=files)

        assert response.status_code == 201
        data = response.json()
        file_ids.append(data["id"])

    # All IDs should be unique
    assert len(file_ids) == len(set(file_ids))


@pytest.mark.asyncio
async def test_upload_with_audio_mp3_content_type(client: AsyncClient, sample_mp3_path: Path):
    """Test upload with audio/mp3 content type."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mp3")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_preserves_original_filename(client: AsyncClient, sample_mp3_path: Path):
    """Test that original filename is preserved in response."""
    original_filename = "my_special_dream_2025.mp3"

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": (original_filename, f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert data["original_filename"] == original_filename


@pytest.mark.asyncio
async def test_upload_saved_filename_format(client: AsyncClient, sample_mp3_path: Path):
    """Test that saved filename follows expected format."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    saved_filename = data["saved_filename"]

    # Should contain UUID and timestamp
    assert saved_filename.endswith(".mp3")
    assert "_" in saved_filename
    assert "T" in saved_filename  # Timestamp format contains T


@pytest.mark.asyncio
async def test_upload_response_format(client: AsyncClient, sample_mp3_path: Path):
    """Test that upload response has correct format."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()

    # Check all required fields are present
    required_fields = ["id", "original_filename", "saved_filename", "file_path", "uploaded_at", "message"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(data["id"], str)
    assert isinstance(data["original_filename"], str)
    assert isinstance(data["saved_filename"], str)
    assert isinstance(data["file_path"], str)
    assert isinstance(data["uploaded_at"], str)
    assert isinstance(data["message"], str)


@pytest.mark.asyncio
async def test_upload_case_insensitive_extension(client: AsyncClient, sample_mp3_path: Path):
    """Test that upload accepts uppercase .MP3 extension."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.MP3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_file_content_integrity(client: AsyncClient, sample_mp3_path: Path):
    """Test that uploaded file content matches original."""
    with open(sample_mp3_path, 'rb') as f:
        original_content = f.read()

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    saved_file_path = Path(data["file_path"])

    # Read saved file and compare
    with open(saved_file_path, 'rb') as f:
        saved_content = f.read()

    assert saved_content == original_content
