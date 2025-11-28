"""
E2E tests for combined workflow endpoints.

Tests the convenience endpoints that combine multiple steps:
- /api/v1/upload-and-transcribe
- /api/v1/upload-transcribe-cleanup

Prerequisites:
- App running in Docker at http://localhost:8000
- Whisper model available
- Ollama running with llama3.2:3b model (for cleanup test)
"""
import pytest
from pathlib import Path
from httpx import AsyncClient
from typing import Tuple

from tests.e2e.e2e_utils import wait_for_transcription, wait_for_cleanup
from tests.conftest import app_is_available

REAL_AUDIO_FILE = Path("tests/fixtures/crocodile.mp3")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_upload_and_transcribe(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test upload-and-transcribe combined endpoint with real Whisper.

    This endpoint combines:
    1. Upload audio file
    2. Trigger transcription

    Returns entry and transcription details immediately.
    """
    client, email = authenticated_e2e_client

    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Upload and transcribe in one request
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        data = {
            "entry_type": "journal",
            "language": "en"
        }
        response = await client.post(
            "/api/v1/upload-and-transcribe",
            files=files,
            data=data
        )

    # Should return 202 with entry and transcription details
    assert response.status_code == 202
    result = response.json()

    # Verify required fields
    assert "entry_id" in result
    assert "transcription_id" in result
    assert "duration_seconds" in result
    assert isinstance(result["duration_seconds"], (int, float))
    assert result["duration_seconds"] > 0

    entry_id = result["entry_id"]
    transcription_id = result["transcription_id"]

    print(f"\n✓ Combined upload and transcribe initiated")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")

    # Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )

    # Verify transcription completed
    assert transcription["transcribed_text"] is not None
    assert len(transcription["transcribed_text"]) > 0

    print(f"✓ Transcription completed: {transcription['transcribed_text'][:80]}...")

    # Verify entry details
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200
    entry = entry_response.json()
    assert entry["id"] == entry_id
    assert entry["original_filename"] == "crocodile.mp3"

    print(f"✓ Upload-and-transcribe workflow successful!")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_upload_transcribe_and_cleanup(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test upload-transcribe-cleanup combined endpoint with real Whisper and Ollama.

    This is the complete workflow endpoint that combines:
    1. Upload audio file
    2. Trigger transcription
    3. Trigger cleanup (after transcription completes)

    Returns entry, transcription, and cleanup details immediately.
    """
    client, email = authenticated_e2e_client

    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Upload, transcribe, and cleanup in one request
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        data = {
            "entry_type": "dream",
            "language": "auto"
        }
        response = await client.post(
            "/api/v1/upload-transcribe-cleanup",
            files=files,
            data=data
        )

    # Should return 202 with entry, transcription, and cleanup details
    assert response.status_code == 202
    result = response.json()

    # Verify required fields
    assert "entry_id" in result
    assert "transcription_id" in result
    assert "cleanup_id" in result
    assert "duration_seconds" in result
    assert isinstance(result["duration_seconds"], (int, float))
    assert result["duration_seconds"] > 0

    entry_id = result["entry_id"]
    transcription_id = result["transcription_id"]
    cleanup_id = result["cleanup_id"]

    print(f"\n✓ Combined upload-transcribe-cleanup initiated")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")
    print(f"  Cleanup ID: {cleanup_id}")

    # Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )

    assert transcription["transcribed_text"] is not None
    assert len(transcription["transcribed_text"]) > 0

    print(f"✓ Transcription completed: {transcription['transcribed_text'][:80]}...")

    # Wait for cleanup to complete (starts after transcription)
    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id
    )

    assert cleaned_entry["cleaned_text"] is not None
    assert len(cleaned_entry["cleaned_text"]) > 0
    assert cleaned_entry["analysis"] is not None

    print(f"✓ Cleanup completed: {cleaned_entry['cleaned_text'][:80]}...")
    print(f"  Themes: {cleaned_entry['analysis'].get('themes', [])}")
    print(f"  Emotions: {cleaned_entry['analysis'].get('emotions', [])}")

    # Verify entry details
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200
    entry = entry_response.json()
    assert entry["id"] == entry_id

    # Verify cleanup is in the cleaned entries list
    cleaned_list_response = await client.get(f"/api/v1/entries/{entry_id}/cleaned")
    assert cleaned_list_response.status_code == 200
    cleaned_list = cleaned_list_response.json()
    assert len(cleaned_list) >= 1

    # Find our cleanup in the list
    cleanup_ids = [c["id"] for c in cleaned_list]
    assert cleanup_id in cleanup_ids

    print(f"\n✓ Complete upload-transcribe-cleanup workflow successful!")
    print(f"  Entry: {entry_id}")
    print(f"  Transcription: {transcription_id}")
    print(f"  Cleanup: {cleanup_id}")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_upload_and_transcribe_error_handling(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """Test error handling for upload-and-transcribe endpoint."""
    client, email = authenticated_e2e_client

    # Test with invalid file type
    files = {"file": ("test.txt", b"not an audio file", "text/plain")}
    data = {"entry_type": "journal", "language": "en"}

    response = await client.post(
        "/api/v1/upload-and-transcribe",
        files=files,
        data=data
    )

    # Should reject invalid file type
    assert response.status_code == 400
    assert "invalid" in response.json()["detail"].lower()

    print(f"✓ Error handling verified - invalid file types rejected")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_upload_transcribe_cleanup_with_custom_parameters(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test upload-transcribe-cleanup with custom AI parameters.

    Tests that custom parameters are accepted and stored:
    - transcription_beam_size: beam size for transcription (7)
    - transcription_temperature: temperature for transcription (0.4)
    - cleanup_temperature: temperature for cleanup (0.6)
    - cleanup_top_p: top_p for cleanup (0.85)
    """
    client, email = authenticated_e2e_client

    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Upload, transcribe, and cleanup with custom parameters
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        data = {
            "entry_type": "dream",
            "language": "en",
            "transcription_beam_size": "7",  # Custom beam size for transcription
            "transcription_temperature": "0.4",  # Custom temperature for transcription
            "cleanup_temperature": "0.6",  # Custom temperature for cleanup
            "cleanup_top_p": "0.85"  # Custom top_p for cleanup
        }
        response = await client.post(
            "/api/v1/upload-transcribe-cleanup",
            files=files,
            data=data
        )

    # Should return 202 with entry, transcription, and cleanup details
    assert response.status_code == 202
    result = response.json()

    entry_id = result["entry_id"]
    transcription_id = result["transcription_id"]
    cleanup_id = result["cleanup_id"]

    print(f"\n✓ Combined upload-transcribe-cleanup with custom parameters initiated")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")
    print(f"  Cleanup ID: {cleanup_id}")

    # Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )

    assert transcription["transcribed_text"] is not None
    print(f"✓ Transcription completed: {transcription['transcribed_text'][:80]}...")

    # Verify transcription parameters were stored
    assert transcription["beam_size"] == 7, "beam_size should be 7"
    assert transcription["temperature"] == 0.4, "transcription temperature should be 0.4"
    print(f"✓ Transcription beam_size parameter verified: {transcription['beam_size']}")
    print(f"✓ Transcription temperature parameter verified: {transcription['temperature']}")

    # Wait for cleanup to complete
    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id
    )

    assert cleaned_entry["cleaned_text"] is not None
    print(f"✓ Cleanup completed: {cleaned_entry['cleaned_text'][:80]}...")

    # Verify cleanup parameters were stored
    assert cleaned_entry["temperature"] == 0.6, "cleanup temperature should be 0.6"
    assert cleaned_entry["top_p"] == 0.85, "cleanup top_p should be 0.85"
    print(f"✓ Cleanup temperature parameter verified: {cleaned_entry['temperature']}")
    print(f"✓ Cleanup top_p parameter verified: {cleaned_entry['top_p']}")

    print(f"\n✓ Complete workflow with custom parameters successful!")
    print(f"  Transcription beam_size: {transcription['beam_size']}")
    print(f"  Transcription temperature: {transcription['temperature']}")
    print(f"  Cleanup temperature: {cleaned_entry['temperature']}")
    print(f"  Cleanup top_p: {cleaned_entry['top_p']}")
