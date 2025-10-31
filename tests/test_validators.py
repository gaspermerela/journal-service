"""
Unit tests for file validators.
"""
import io
import pytest
from fastapi import HTTPException, UploadFile
from unittest.mock import AsyncMock

from app.utils.validators import validate_audio_file
from app.config import Settings


@pytest.mark.asyncio
async def test_validate_audio_file_valid_mp3(sample_mp3_path):
    """Test validation succeeds with valid MP3 file."""
    # Create UploadFile from sample MP3
    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    # Should not raise exception
    await validate_audio_file(file)

    # File position should be reset to 0
    position = file.file.tell()
    assert position == 0


@pytest.mark.asyncio
async def test_validate_audio_file_no_file():
    """Test validation fails when no file is provided."""
    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(None)

    assert exc_info.value.status_code == 400
    assert "No file provided" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_audio_file_no_filename():
    """Test validation fails when filename is missing."""
    file = UploadFile(
        file=io.BytesIO(b"test data"),
        filename="",
        headers={"content-type": "audio/mpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 400
    assert "No filename provided" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_audio_file_invalid_extension():
    """Test validation fails with invalid file extension."""
    file = UploadFile(
        file=io.BytesIO(b"test data"),
        filename="test.txt",
        headers={"content-type": "audio/mpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 400
    assert "Invalid file type" in exc_info.value.detail
    assert ".mp3" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_audio_file_invalid_content_type():
    """Test validation fails with invalid content type."""
    file = UploadFile(
        file=io.BytesIO(b"test data"),
        filename="test.mp3",
        headers={"content-type": "text/plain"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 400
    assert "Invalid content type" in exc_info.value.detail


@pytest.mark.asyncio
async def test_validate_audio_file_too_large(test_settings: Settings):
    """Test validation fails when file exceeds size limit."""
    # Create data larger than max size
    max_bytes = test_settings.max_file_size_bytes
    large_data = b"x" * (max_bytes + 1024)

    file = UploadFile(
        file=io.BytesIO(large_data),
        filename="large_dream.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 413
    assert "too large" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_audio_file_empty():
    """Test validation fails with empty file."""
    file = UploadFile(
        file=io.BytesIO(b""),
        filename="empty.mp3",
        headers={"content-type": "audio/mpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_validate_audio_file_with_audio_mp3_content_type(sample_mp3_path):
    """Test validation succeeds with audio/mp3 content type."""
    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.mp3",
        headers={"content-type": "audio/mp3"}
    )

    # Should not raise exception
    await validate_audio_file(file)


@pytest.mark.asyncio
async def test_validate_audio_file_case_insensitive_extension(sample_mp3_path):
    """Test validation works with uppercase extension."""
    with open(sample_mp3_path, 'rb') as f:
        content = f.read()

    file = UploadFile(
        file=io.BytesIO(content),
        filename="test_dream.MP3",
        headers={"content-type": "audio/mpeg"}
    )

    # Should not raise exception (extension check is case-insensitive)
    await validate_audio_file(file)


@pytest.mark.asyncio
async def test_validate_audio_file_no_extension():
    """Test validation fails when filename has no extension."""
    file = UploadFile(
        file=io.BytesIO(b"test data"),
        filename="testfile",
        headers={"content-type": "audio/mpeg"}
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_audio_file(file)

    assert exc_info.value.status_code == 400
    assert "Invalid file type" in exc_info.value.detail
