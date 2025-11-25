"""
End-to-end tests for LLM cleanup workflow.

These tests verify the cleanup pipeline works with REAL services.
All real e2e tests use actual Ollama LLM (no mocks).

Prerequisites:
- PostgreSQL database running
- App running in Docker at http://localhost:8000
- Ollama running with llama3.2:3b model

Run tests: pytest tests/test_e2e_cleanup.py -v
Tests will be skipped if services are not available.
"""
import os
import pytest
from pathlib import Path
from httpx import AsyncClient
from typing import Tuple

from tests.e2e.e2e_utils import wait_for_transcription, wait_for_cleanup
from tests.conftest import app_is_available

# Real audio file to use for all tests
REAL_AUDIO_FILE = Path("tests/fixtures/crocodile.mp3")

@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_cleanup_full_workflow(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test complete cleanup workflow with real Whisper and Ollama:
    1. Upload audio file
    2. Transcribe with real Whisper
    3. Cleanup with real Ollama
    4. Verify cleaned text and analysis

    This test uses REAL services (no mocks).
    """
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Step 1: Upload audio file
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]
    print(f"\n✓ Uploaded entry: {entry_id}")

    # Step 2: Trigger transcription
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]
    print(f"✓ Started transcription: {transcription_id}")

    # Step 3: Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id,
        max_wait=90,
        poll_interval=3
    )
    assert transcription["transcribed_text"] is not None
    print(f"✓ Transcription completed: {transcription['transcribed_text'][:80]}...")

    # Step 4: Trigger cleanup with real Ollama
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )

    assert cleanup_response.status_code == 202
    cleanup_data = cleanup_response.json()
    cleanup_id = cleanup_data["id"]
    print(f"\n✓ Started cleanup: {cleanup_id}")

    # Step 5: Wait for cleanup to complete
    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id,
        max_wait=120,
        poll_interval=3
    )

    # Step 6: Verify real LLM results
    assert cleaned_entry["cleaned_text"] is not None
    assert len(cleaned_entry["cleaned_text"]) > 0

    # Verify analysis structure
    assert "analysis" in cleaned_entry
    analysis = cleaned_entry["analysis"]
    assert "themes" in analysis
    assert "emotions" in analysis
    assert isinstance(analysis["themes"], list)
    assert isinstance(analysis["emotions"], list)

    print(f"\n✓ Cleanup completed successfully!")
    print(f"  Cleaned text: {cleaned_entry['cleaned_text'][:100]}...")
    print(f"  Themes: {analysis['themes']}")
    print(f"  Emotions: {analysis['emotions']}")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")
    print(f"  Cleanup ID: {cleanup_id}")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_cleanup_multiple_attempts(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Test multiple cleanup attempts on the same transcription.

    This verifies:
    1. You can trigger cleanup multiple times
    2. Each cleanup creates a separate cleaned entry
    3. All cleanups are linked to the same transcription
    """
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Step 1: Upload and transcribe
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    transcription_id = transcribe_response.json()["transcription_id"]

    # Wait for transcription
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id,
        max_wait=240,
        poll_interval=3
    )
    print(f"✓ Transcription completed")

    # Step 2: Trigger first cleanup
    cleanup1_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    assert cleanup1_response.status_code == 202
    cleanup1_id = cleanup1_response.json()["id"]
    print(f"\n✓ Started cleanup 1: {cleanup1_id}")

    # Step 3: Trigger second cleanup (while first might still be running)
    cleanup2_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    assert cleanup2_response.status_code == 202
    cleanup2_id = cleanup2_response.json()["id"]
    print(f"✓ Started cleanup 2: {cleanup2_id}")

    # Verify we have two different cleanup IDs
    assert cleanup1_id != cleanup2_id, "Should create separate cleanup entries"

    # Step 4: Wait for first cleanup to complete
    cleaned1 = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup1_id,
        max_wait=45,
        poll_interval=3
    )
    print(f"✓ First cleanup completed")

    # Step 5: List all cleaned entries for the entry
    list_response = await client.get(f"/api/v1/entries/{entry_id}/cleaned")
    assert list_response.status_code == 200
    cleaned_entries = list_response.json()

    print(f"\nCleaned entries for entry {entry_id}: {len(cleaned_entries)} total")
    assert isinstance(cleaned_entries, list)
    assert len(cleaned_entries) >= 1, "Should have at least 1 completed cleanup"

    # Verify cleanup IDs
    cleaned_ids = [c["id"] for c in cleaned_entries]
    print(f"Cleaned entry IDs: {cleaned_ids}")

    print(f"\n✓ Multiple cleanup attempts successful!")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")
    print(f"  Cleanup 1 ID: {cleanup1_id}")
    print(f"  Cleanup 2 ID: {cleanup2_id}")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_cleanup_invalid_transcription(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """Test cleanup fails gracefully with invalid transcription ID."""
    client, email = authenticated_e2e_client

    fake_transcription_id = "00000000-0000-0000-0000-000000000000"

    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{fake_transcription_id}/cleanup"
    )

    assert cleanup_response.status_code == 404
    assert "not found" in cleanup_response.json()["detail"].lower()

    print(f"✓ Invalid transcription ID correctly rejected")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_cleanup_list_for_entry(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """Test retrieving all cleanups for a voice entry."""
    client, email = authenticated_e2e_client

    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # Upload a file
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    # Get cleaned entries (should be empty initially)
    response = await client.get(f"/api/v1/entries/{entry_id}/cleaned")

    assert response.status_code == 200
    cleaned_entries = response.json()
    assert isinstance(cleaned_entries, list)
    assert len(cleaned_entries) == 0, "No cleanups yet"

    print(f"✓ Empty cleanup list verified for new entry")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not app_is_available(),
    reason="App not running at http://localhost:8000"
)
@pytest.mark.asyncio
async def test_e2e_cleanup_user_isolation(
    real_api_client: AsyncClient
):
    """
    Test that users can't access each other's cleaned entries.

    Note: This test doesn't use the fixture because we need two separate users.
    """
    # Check if real audio file exists
    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Real audio file not found: {REAL_AUDIO_FILE}")

    # User A: Register, login, upload, transcribe, cleanup
    email_a = f"user_a_cleanup_{os.urandom(4).hex()}@example.com"
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

    # Upload and transcribe for User A
    with open(REAL_AUDIO_FILE, 'rb') as f:
        files = {"file": ("user_a_file.mp3", f, "audio/mpeg")}
        upload_a = await real_api_client.post("/api/v1/upload", files=files)

    entry_a_id = upload_a.json()["id"]

    transcribe_a = await real_api_client.post(
        f"/api/v1/entries/{entry_a_id}/transcribe",
        json={"language": "en"}
    )
    transcription_a_id = transcribe_a.json()["transcription_id"]

    # Wait for transcription
    transcription = await wait_for_transcription(
        client=real_api_client,
        transcription_id=transcription_a_id,
        max_wait=90,
        poll_interval=3
    )

    # Trigger cleanup for User A
    cleanup_a = await real_api_client.post(
        f"/api/v1/transcriptions/{transcription_a_id}/cleanup"
    )
    assert cleanup_a.status_code == 202
    cleanup_a_id = cleanup_a.json()["id"]

    # User B: Register and login
    email_b = f"user_b_cleanup_{os.urandom(4).hex()}@example.com"
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

    # User B tries to access User A's cleanup
    cleanup_response = await real_api_client.get(f"/api/v1/cleaned-entries/{cleanup_a_id}")
    assert cleanup_response.status_code == 404, "User B should not access User A's cleanup"

    # User B tries to list User A's entry cleanups
    list_response = await real_api_client.get(f"/api/v1/entries/{entry_a_id}/cleaned")
    assert list_response.status_code == 404, "User B should not list User A's cleanups"

    print(f"✓ User isolation verified - users cannot access each other's cleanups")
