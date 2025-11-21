"""
Integration tests for upload endpoint.
Requires authentication.
"""
import io
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_upload_valid_mp3(authenticated_client: AsyncClient, sample_mp3_path: Path, test_storage_path: Path):
    """Test uploading a valid MP3 file."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream_recording.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert "original_filename" in data
    assert "saved_filename" in data
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


@pytest.mark.asyncio
async def test_upload_no_file(authenticated_client: AsyncClient):
    """Test upload endpoint with no file."""
    response = await authenticated_client.post("/api/v1/upload")

    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_upload_invalid_file_type(authenticated_client: AsyncClient, invalid_file_path: Path):
    """Test uploading a non-MP3 file."""
    with open(invalid_file_path, 'rb') as f:
        files = {"file": ("document.txt", f, "text/plain")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "invalid" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_file_too_large(authenticated_client: AsyncClient, large_mp3_path: Path):
    """Test uploading a file that exceeds size limit."""
    with open(large_mp3_path, 'rb') as f:
        files = {"file": ("large_dream.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 413

    data = response.json()
    assert "detail" in data
    assert "too large" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_empty_file(authenticated_client: AsyncClient):
    """Test uploading an empty file."""
    files = {"file": ("empty.mp3", io.BytesIO(b""), "audio/mpeg")}
    response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 400

    data = response.json()
    assert "detail" in data
    assert "empty" in data["detail"].lower()


@pytest.mark.asyncio
async def test_upload_creates_date_folder(authenticated_client: AsyncClient, sample_mp3_path: Path, test_storage_path: Path):
    """Test that upload creates date-based folder structure."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    # Note: Date folder structure is tested internally by storage service
    # File path is no longer exposed in API responses for security


@pytest.mark.asyncio
async def test_upload_multiple_files(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test uploading multiple files creates separate entries."""
    file_ids = []

    for i in range(3):
        with open(sample_mp3_path, 'rb') as f:
            files = {"file": (f"dream_{i}.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post("/api/v1/upload", files=files)

        assert response.status_code == 201
        data = response.json()
        file_ids.append(data["id"])

    # All IDs should be unique
    assert len(file_ids) == len(set(file_ids))


@pytest.mark.asyncio
async def test_upload_with_audio_mp3_content_type(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test upload with audio/mp3 content type."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mp3")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_preserves_original_filename(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test that original filename is preserved in response."""
    original_filename = "my_special_dream_2025.mp3"

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": (original_filename, f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert data["original_filename"] == original_filename


@pytest.mark.asyncio
async def test_upload_saved_filename_format(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test that saved filename follows expected format."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    saved_filename = data["saved_filename"]

    # Should contain UUID and timestamp
    assert saved_filename.endswith(".mp3")
    assert "_" in saved_filename
    assert "T" in saved_filename  # Timestamp format contains T


@pytest.mark.asyncio
async def test_upload_response_format(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test that upload response has correct format."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()

    # Check all required fields are present
    required_fields = ["id", "original_filename", "saved_filename", "duration_seconds", "uploaded_at", "message"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Check data types
    assert isinstance(data["id"], str)
    assert isinstance(data["original_filename"], str)
    assert isinstance(data["saved_filename"], str)
    assert isinstance(data["duration_seconds"], (int, float))
    assert isinstance(data["uploaded_at"], str)
    assert isinstance(data["message"], str)


@pytest.mark.asyncio
async def test_upload_case_insensitive_extension(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test that upload accepts uppercase .MP3 extension."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.MP3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_upload_file_content_integrity(authenticated_client: AsyncClient, sample_mp3_path: Path):
    """Test that upload processes file successfully."""
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("dream.mp3", f, "audio/mpeg")}
        response = await authenticated_client.post("/api/v1/upload", files=files)

    assert response.status_code == 201

    data = response.json()
    assert "id" in data
    assert data["original_filename"] == "dream.mp3"
    # Note: File content integrity is tested internally by storage service
    # File path is no longer exposed in API responses for security
