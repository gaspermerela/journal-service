"""
Integration tests for audio download endpoint.
Tests authentication, authorization, file serving, and error handling.
"""
import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.models.voice_entry import VoiceEntry


@pytest.mark.asyncio
async def test_download_own_audio_success(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that authenticated user can download their own audio file."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}/audio")

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert "Accept-Ranges" in response.headers
    assert response.headers["Accept-Ranges"] == "bytes"
    assert "Cache-Control" in response.headers
    assert "private" in response.headers["Cache-Control"]
    assert "max-age=3600" in response.headers["Cache-Control"]
    assert "immutable" in response.headers["Cache-Control"]
    assert "Content-Disposition" in response.headers
    assert "inline" in response.headers["Content-Disposition"]
    assert ".wav" in response.headers["Content-Disposition"]


@pytest.mark.asyncio
async def test_download_audio_not_authenticated(client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that unauthenticated requests are rejected."""
    response = await client.get(f"/api/v1/entries/{sample_voice_entry.id}/audio")

    # JWT middleware returns 403 for missing/invalid tokens
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_download_other_user_audio_forbidden(
    authenticated_client: AsyncClient,
    db_session,
    test_storage_path: Path
):
    """Test that user cannot download another user's audio file."""
    from app.schemas.auth import UserCreate
    from app.services.database import db_service

    # Create another user using proper service
    other_user_data = UserCreate(
        email="other@example.com",
        password="OtherPassword123!"
    )
    other_user = await db_service.create_user(db_session, other_user_data)
    await db_session.commit()
    await db_session.refresh(other_user)

    # Create entry for other user with a valid file path
    audio_file = test_storage_path / "other_user_audio.wav"
    audio_file.write_text("fake audio data")

    other_entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="other_dream.m4a",
        saved_filename="other_saved.wav",
        file_path=str(audio_file),
        entry_type="dream",
        duration_seconds=60.0,
        user_id=other_user.id
    )
    db_session.add(other_entry)
    await db_session.commit()

    # Try to download other user's audio
    response = await authenticated_client.get(f"/api/v1/entries/{other_entry.id}/audio")

    # Should return 404 (not 403) to avoid leaking entry existence
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_download_nonexistent_entry(authenticated_client: AsyncClient):
    """Test downloading audio for non-existent entry returns 404."""
    non_existent_id = uuid.uuid4()
    response = await authenticated_client.get(f"/api/v1/entries/{non_existent_id}/audio")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_download_audio_file_missing_on_disk(
    authenticated_client: AsyncClient,
    db_session,
    test_user
):
    """Test that missing file on disk returns 404 and logs error."""
    # Create entry with non-existent file path
    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="missing.m4a",
        saved_filename="missing.wav",
        file_path="/nonexistent/path/missing.wav",
        entry_type="dream",
        duration_seconds=60.0,
        user_id=test_user.id
    )
    db_session.add(entry)
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/entries/{entry.id}/audio")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not available" in data["detail"].lower()


@pytest.mark.asyncio
async def test_download_audio_invalid_uuid(authenticated_client: AsyncClient):
    """Test that invalid UUID returns 422 validation error."""
    response = await authenticated_client.get("/api/v1/entries/invalid-uuid/audio")

    assert response.status_code == 422  # FastAPI validation error


@pytest.mark.asyncio
async def test_download_audio_content_disposition_sanitized(
    authenticated_client: AsyncClient,
    db_session,
    test_user,
    test_storage_path: Path
):
    """Test that filename in Content-Disposition is sanitized."""
    # Create entry with special characters in filename
    audio_file = test_storage_path / "special.wav"
    audio_file.write_text("fake audio")

    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename='my"dream<test>.m4a',  # Special characters
        saved_filename="special.wav",
        file_path=str(audio_file),
        entry_type="dream",
        duration_seconds=60.0,
        user_id=test_user.id
    )
    db_session.add(entry)
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/entries/{entry.id}/audio")

    assert response.status_code == 200
    content_disposition = response.headers["Content-Disposition"]

    # Special characters should be removed
    assert '"' not in content_disposition or content_disposition.count('"') == 2  # Only quotes around filename
    assert "<" not in content_disposition
    assert ">" not in content_disposition
    assert ".wav" in content_disposition  # Extension should be .wav


@pytest.mark.asyncio
async def test_download_audio_response_headers(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that response headers are correctly set for audio streaming."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}/audio")

    assert response.status_code == 200

    # Check MIME type
    assert response.headers["content-type"] == "audio/wav"

    # Check range request support
    assert response.headers["Accept-Ranges"] == "bytes"

    # Check caching headers
    cache_control = response.headers["Cache-Control"]
    assert "private" in cache_control
    assert "max-age=3600" in cache_control
    assert "immutable" in cache_control

    # Check content disposition
    content_disposition = response.headers["Content-Disposition"]
    assert "inline" in content_disposition
    assert "filename=" in content_disposition


@pytest.mark.asyncio
async def test_download_audio_wav_extension_forced(
    authenticated_client: AsyncClient,
    db_session,
    test_user,
    test_storage_path: Path
):
    """Test that downloaded file always has .wav extension regardless of original."""
    # Create entry with .m4a original filename
    audio_file = test_storage_path / "test.wav"
    audio_file.write_text("fake audio")

    entry = VoiceEntry(
        id=uuid.uuid4(),
        original_filename="dream.m4a",  # Original was m4a
        saved_filename="test.wav",
        file_path=str(audio_file),
        entry_type="dream",
        duration_seconds=60.0,
        user_id=test_user.id
    )
    db_session.add(entry)
    await db_session.commit()

    response = await authenticated_client.get(f"/api/v1/entries/{entry.id}/audio")

    assert response.status_code == 200

    # Filename should be .wav (preprocessed format)
    content_disposition = response.headers["Content-Disposition"]
    assert "dream.wav" in content_disposition
    assert ".m4a" not in content_disposition


@pytest.mark.asyncio
async def test_download_audio_content_length(authenticated_client: AsyncClient, sample_voice_entry: VoiceEntry):
    """Test that Content-Length header is present."""
    response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}/audio")

    assert response.status_code == 200
    # FileResponse should automatically set Content-Length
    assert "Content-Length" in response.headers or "Transfer-Encoding" in response.headers
