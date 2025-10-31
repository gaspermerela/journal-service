"""
Unit tests for storage service.
"""
import io
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from fastapi import HTTPException, UploadFile

from app.services.storage import StorageService


@pytest.fixture
def storage_service(test_storage_path):
    """Create storage service with test storage path."""
    service = StorageService()
    service.base_path = test_storage_path
    return service


def test_generate_filename():
    """Test filename generation with UUID and timestamp."""
    service = StorageService()
    file_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")

    filename = service._generate_filename(file_id)

    # Should contain UUID
    assert str(file_id) in filename
    # Should end with .mp3
    assert filename.endswith(".mp3")
    # Should contain timestamp in format YYYYMMDDTHHmmss
    assert "_" in filename
    parts = filename.split("_")
    assert len(parts) == 2
    timestamp_part = parts[1].replace(".mp3", "")
    # Verify timestamp format
    assert len(timestamp_part) == 15  # YYYYMMDDTHHmmss
    assert "T" in timestamp_part


def test_get_date_folder():
    """Test date folder name generation."""
    service = StorageService()

    folder_name = service._get_date_folder()

    # Should be in format YYYY-MM-DD
    assert len(folder_name) == 10
    assert folder_name.count("-") == 2

    # Should be today's date
    expected = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert folder_name == expected


def test_ensure_directory_exists(storage_service: StorageService, test_storage_path: Path):
    """Test directory creation."""
    test_dir = test_storage_path / "test_subfolder" / "nested"

    assert not test_dir.exists()

    storage_service._ensure_directory_exists(test_dir)

    assert test_dir.exists()
    assert test_dir.is_dir()


def test_ensure_directory_exists_already_exists(storage_service: StorageService, test_storage_path: Path):
    """Test directory creation when directory already exists."""
    test_dir = test_storage_path / "existing_dir"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Should not raise exception
    storage_service._ensure_directory_exists(test_dir)

    assert test_dir.exists()


@pytest.mark.asyncio
async def test_save_file_success(storage_service: StorageService, sample_mp3_path: Path):
    """Test successful file save operation."""
    file_id = uuid.uuid4()

    # Create UploadFile from sample MP3
    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    saved_filename, file_path = await storage_service.save_file(file, file_id)

    # Check filename format
    assert str(file_id) in saved_filename
    assert saved_filename.endswith(".mp3")

    # Check file was saved
    assert Path(file_path).exists()

    # Check file contains expected content
    with open(file_path, 'rb') as f:
        saved_content = f.read()
    assert saved_content == content

    # Check file permissions (should be 644 on Unix systems)
    if os.name != 'nt':  # Skip on Windows
        stat_info = os.stat(file_path)
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == '644'


@pytest.mark.asyncio
async def test_save_file_creates_date_folder(storage_service: StorageService, sample_mp3_path: Path):
    """Test that save_file creates date-based folder structure."""
    file_id = uuid.uuid4()

    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    saved_filename, file_path = await storage_service.save_file(file, file_id)

    # Check that file is in date-based folder
    expected_folder = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert expected_folder in file_path


@pytest.mark.asyncio
async def test_save_file_atomic_operation(storage_service: StorageService, sample_mp3_path: Path):
    """Test that file saving uses atomic write operation (temp file then move)."""
    file_id = uuid.uuid4()

    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    saved_filename, file_path = await storage_service.save_file(file, file_id)

    # Check that no .tmp files remain
    temp_files = list(Path(file_path).parent.glob("*.tmp"))
    assert len(temp_files) == 0

    # Check final file exists
    assert Path(file_path).exists()


@pytest.mark.asyncio
async def test_save_file_large_file(storage_service: StorageService):
    """Test saving large file with chunked reading."""
    file_id = uuid.uuid4()

    # Create 5MB file
    large_content = b"x" * (5 * 1024 * 1024)

    file = UploadFile(
        file=io.BytesIO(large_content),
        filename="large_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    saved_filename, file_path = await storage_service.save_file(file, file_id)

    # Verify file size
    assert Path(file_path).stat().st_size == len(large_content)


@pytest.mark.asyncio
async def test_delete_file_success(storage_service: StorageService, test_storage_path: Path):
    """Test successful file deletion."""
    # Create a test file
    test_file = test_storage_path / "test_delete.mp3"
    test_file.write_bytes(b"test content")

    assert test_file.exists()

    result = await storage_service.delete_file(str(test_file))

    assert result is True
    assert not test_file.exists()


@pytest.mark.asyncio
async def test_delete_file_not_found(storage_service: StorageService, test_storage_path: Path):
    """Test deletion of non-existent file."""
    non_existent_path = test_storage_path / "non_existent.mp3"

    result = await storage_service.delete_file(str(non_existent_path))

    assert result is False


@pytest.mark.asyncio
async def test_delete_file_handles_errors(storage_service: StorageService, test_storage_path: Path):
    """Test that delete_file handles errors gracefully."""
    # Try to delete with invalid path
    result = await storage_service.delete_file("/invalid/path/that/does/not/exist.mp3")

    # Should return False instead of raising exception
    assert result is False


@pytest.mark.asyncio
async def test_save_file_cleanup_on_error(storage_service: StorageService, test_storage_path: Path):
    """Test that temp files are cleaned up on error."""
    file_id = uuid.uuid4()

    # Create a mock file that will cause an error during save
    file = UploadFile(
        file=io.BytesIO(b"test"),
        filename="test.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    # Mock the move operation to fail
    with patch('shutil.move', side_effect=Exception("Disk full")):
        with pytest.raises(HTTPException) as exc_info:
            await storage_service.save_file(file, file_id)

        assert exc_info.value.status_code == 500
        assert "Failed to save file" in exc_info.value.detail

    # Check that no .tmp files remain
    temp_files = list(test_storage_path.rglob("*.tmp"))
    assert len(temp_files) == 0


def test_storage_service_uses_configured_base_path(test_settings):
    """Test that StorageService uses the configured base path."""
    service = StorageService()

    # Should use the path from settings
    expected_path = Path(test_settings.AUDIO_STORAGE_PATH)
    assert service.base_path == expected_path
