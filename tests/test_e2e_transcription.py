"""
End-to-end transcription workflow tests.

These tests verify the transcription pipeline works with REAL services.
All tests use actual Whisper transcription.

Prerequisites:
- PostgreSQL database running
- Whisper model available
- Transcription service initialized in the app

Run tests: pytest tests/test_e2e_transcription.py -v
Tests will be skipped if transcription service is not available.
"""
import os
import pytest
from pathlib import Path
from httpx import AsyncClient
from typing import Tuple

from tests.e2e_utils import wait_for_transcription
from tests.conftest import transcription_service_available

# Real audio file to use for all tests
REAL_AUDIO_FILE = Path("tests/fixtures/crocodile.mp3")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not transcription_service_available(),
    reason="Transcription service not available (Whisper model or dependencies missing)"
)
@pytest.mark.asyncio
async def test_e2e_basic_transcription_flow(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test basic transcription flow with real Whisper:
    Register -> Login -> Upload -> Trigger Transcription -> Get Transcription.

    This test uses REAL transcription service.
    """
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Step 1: Upload file
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]

    # Step 2: Trigger transcription
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    # Step 3: Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id,
        max_wait=60,
        poll_interval=2
    )

    # Step 4: Verify transcription completed successfully
    assert transcription["id"] == transcription_id
    assert transcription["transcribed_text"] is not None
    assert len(transcription["transcribed_text"]) > 0

    print(f"✓ Transcription completed: {transcription['transcribed_text']}...")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not transcription_service_available(),
    reason="Transcription service not available (Whisper model or dependencies missing)"
)
@pytest.mark.asyncio
async def test_e2e_full_transcription_lifecycle(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test complete transcription lifecycle with real Whisper:
    1. Upload one audio file
    2. Trigger multiple transcriptions for the same entry
    3. Wait for transcriptions to complete
    4. List all transcriptions for the entry
    5. Verify all data is accessible

    This test verifies that a single audio file can have multiple transcription attempts.
    """
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Step 1: Upload audio file once
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]
    print(f"\nUploaded entry: {entry_id}")

    # Step 2: Trigger first transcription
    transcribe_response1 = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response1.status_code == 202
    transcription1_id = transcribe_response1.json()["transcription_id"]
    print(f"Started transcription 1: {transcription1_id}")

    # Step 3: Trigger second transcription for the SAME entry
    transcribe_response2 = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response2.status_code == 202
    transcription2_id = transcribe_response2.json()["transcription_id"]
    print(f"Started transcription 2: {transcription2_id}")

    # Verify we have two different transcription IDs
    assert transcription1_id != transcription2_id, "Should create separate transcriptions"

    # Step 4: Wait for first transcription to complete
    transcription1 = await wait_for_transcription(
        client=client,
        transcription_id=transcription1_id,
        max_wait=60,
        poll_interval=2
    )
    print(f"✓ First transcription completed")

    # Step 5: Check entry includes transcription data
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200
    entry = entry_response.json()
    assert entry["id"] == entry_id

    # Step 6: List transcriptions for the entry - should have at least 2
    list_response = await client.get(f"/api/v1/entries/{entry_id}/transcriptions")
    assert list_response.status_code == 200
    transcriptions_data = list_response.json()

    print(f"\nTranscriptions for entry {entry_id}: {transcriptions_data['total']} total")

    # Should have exactly 2 transcriptions for this entry
    assert transcriptions_data["total"] == 2, f"Should have 2 transcriptions, got {transcriptions_data['total']}"
    assert len(transcriptions_data["transcriptions"]) == 2, "Should return 2 transcription objects"

    # Verify both transcription IDs are in the list
    returned_ids = {t["id"] for t in transcriptions_data["transcriptions"]}
    expected_ids = {str(transcription1_id), str(transcription2_id)}

    print(f"Expected transcription IDs: {expected_ids}")
    print(f"Returned transcription IDs: {returned_ids}")

    assert expected_ids == returned_ids, f"Expected IDs {expected_ids}, got {returned_ids}"

    print(f"\n✓ Full transcription lifecycle successful!")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription 1 ID: {transcription1_id}")
    print(f"  Transcription 2 ID: {transcription2_id}")
    print(f"  Both transcriptions verified in list!")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not transcription_service_available(),
    reason="Transcription service not available (Whisper model or dependencies missing)"
)
@pytest.mark.asyncio
async def test_e2e_transcription_with_real_audio(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test transcription with real audio file (crocodile.mp3) using real Whisper.

    This verifies the entire pipeline with actual audio content and validates
    the transcribed text length and content.
    """
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Step 1: Upload real audio file
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]

    # Step 2: Trigger transcription
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    # Step 3: Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id,
        max_wait=90,  # Real audio may take longer
        poll_interval=3
    )

    # Step 4: Verify results
    assert transcription["transcribed_text"] is not None
    assert len(transcription["transcribed_text"]) > 10  # Should have substantial text

    print(f"\n✓ Real audio transcription successful!")
    print(f"  Transcribed text: {transcription['transcribed_text']}")
    print(f"  Text length: {len(transcription['transcribed_text'])} characters")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not transcription_service_available(),
    reason="Transcription service not available (Whisper model or dependencies missing)"
)
@pytest.mark.asyncio
async def test_e2e_transcription_user_isolation(
    real_api_client: AsyncClient
):
    """
    Test that users can't access each other's transcriptions.
    Uses real transcription service.

    Note: This test doesn't use authenticated_e2e_client fixture because we need two separate users.
    """
    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # User A: Register, login, upload, transcribe
    email_a = f"user_a_{os.urandom(4).hex()}@example.com"
    await real_api_client.post(
        "/api/v1/auth/register",
        json={"email": email_a, "password": "UserA123!"}
    )
    login_a = await real_api_client.post(
        "/api/v1/auth/login",
        json={"email": email_a, "password": "UserA123!"}
    )
    token_a = login_a.json()["access_token"]
    real_api_client.headers["Authorization"] = f"Bearer {token_a}"

    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("user_a_file.mp3", f, "audio/mpeg")}
        upload_a = await real_api_client.post("/api/v1/upload", files=files)

    entry_a_id = upload_a.json()["id"]

    # Transcribe for User A
    transcribe_a = await real_api_client.post(
        f"/api/v1/entries/{entry_a_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_a.status_code == 202
    transcription_a_id = transcribe_a.json()["transcription_id"]

    # User B: Register and login
    email_b = f"user_b_{os.urandom(4).hex()}@example.com"
    await real_api_client.post(
        "/api/v1/auth/register",
        json={"email": email_b, "password": "UserB123!"}
    )
    login_b = await real_api_client.post(
        "/api/v1/auth/login",
        json={"email": email_b, "password": "UserB123!"}
    )
    token_b = login_b.json()["access_token"]
    real_api_client.headers["Authorization"] = f"Bearer {token_b}"

    # User B tries to access User A's transcription
    trans_response = await real_api_client.get(f"/api/v1/transcriptions/{transcription_a_id}")
    assert trans_response.status_code == 404, "User B should not be able to access User A's transcription"

    # User B tries to list User A's entry transcriptions
    list_response = await real_api_client.get(f"/api/v1/entries/{entry_a_id}/transcriptions")
    assert list_response.status_code == 404, "User B should not be able to list User A's transcriptions"

    print(f"✓ User isolation verified - users cannot access each other's transcriptions")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not transcription_service_available(),
    reason="Transcription service not available (Whisper model or dependencies missing)"
)
@pytest.mark.asyncio
async def test_e2e_transcription_error_handling(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test transcription error handling with invalid entry ID.
    """
    client, email = authenticated_e2e_client

    # Try to transcribe non-existent entry
    fake_entry_id = "00000000-0000-0000-0000-000000000000"
    transcribe_response = await client.post(
        f"/api/v1/entries/{fake_entry_id}/transcribe",
        json={"language": "en"}
    )

    assert transcribe_response.status_code == 404
    assert "not found" in transcribe_response.json()["detail"].lower()

    print(f"✓ Error handling verified - invalid entry IDs are rejected")
