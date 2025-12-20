"""
Full end-to-end workflow tests: Upload → Transcribe → Cleanup → Retrieve

These tests verify the complete Phase 1-4 pipeline works together.

Prerequisites for real e2e tests:
- PostgreSQL database running
- Whisper model available
- Ollama running with llama3.2:3b model

Run all tests: pytest tests/test_e2e_full_workflow.py
Run only mocked tests: pytest tests/test_e2e_full_workflow.py -k "not real"
"""
import asyncio
import os
import pytest
from pathlib import Path
from httpx import AsyncClient
from typing import Tuple

from tests.e2e.e2e_utils import wait_for_transcription, wait_for_cleanup
from tests.conftest import app_is_available


@pytest.mark.asyncio
async def test_e2e_workflow_api_structure(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    Test complete API workflow structure (with mocks).
    Verifies all endpoints are accessible and return expected structure.
    """
    from app.main import app
    from unittest.mock import AsyncMock, patch

    app.state.transcription_service = mock_transcription_service

    # Step 1: Register user
    register_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "workflow_test@example.com", "password": "Workflow123!"}
    )
    assert register_response.status_code == 201

    # Step 2: Login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "workflow_test@example.com", "password": "Workflow123!"}
    )
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 3: Upload audio file
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    upload_data = upload_response.json()
    assert "id" in upload_data
    entry_id = upload_data["id"]

    # Step 4: Trigger transcription
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    # Step 5: Check transcription status endpoint works
    await asyncio.sleep(0.5)
    trans_status_response = await client.get(
        f"/api/v1/transcriptions/{transcription_id}"
    )
    assert trans_status_response.status_code == 200
    assert "id" in trans_status_response.json()

    # Step 6: Get entry (should include metadata)
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200
    entry_data = entry_response.json()
    assert entry_data["id"] == entry_id
    assert entry_data["original_filename"] == "recording.mp3"

    # Step 7: List transcriptions for entry
    transcriptions_response = await client.get(
        f"/api/v1/entries/{entry_id}/transcriptions"
    )
    assert transcriptions_response.status_code == 200
    transcriptions_data = transcriptions_response.json()
    assert "transcriptions" in transcriptions_data
    assert "total" in transcriptions_data
    assert transcriptions_data["total"] >= 1

    # Step 8: List cleaned entries for entry (should be empty)
    cleaned_response = await client.get(f"/api/v1/entries/{entry_id}/cleaned")
    assert cleaned_response.status_code == 200
    assert isinstance(cleaned_response.json(), list)


@pytest.mark.e2e_real
@pytest.mark.skipif(not app_is_available(), reason="App not running at http://localhost:8000")
@pytest.mark.asyncio
async def test_e2e_real_complete_workflow(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Real end-to-end test of the complete workflow with actual services.

    This test:
    1. Uploads real audio
    2. Transcribes with real Whisper
    3. Cleans with real Ollama
    4. Retrieves and validates all results

    Prerequisites:
    - Ollama: ollama serve
    - Model: ollama pull llama3.2:3b
    - Whisper model files in place
    """
    client, email = authenticated_e2e_client

    # Step 2: Upload real audio file
    audio_file = Path("tests/fixtures/crocodile.mp3")
    if not audio_file.exists():
        pytest.skip("Real audio file not found")

    with open(audio_file, 'rb') as f:
        files = {"file": ("crocodile.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]

    # Step 3: Trigger transcription
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    # Step 4: Wait for transcription to complete
    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )
    assert transcription["transcribed_text"] is not None
    assert len(transcription["transcribed_text"]) > 0

    print(f"✓ Transcription completed: {transcription['transcribed_text'][:80]}...")

    # Step 5: Trigger LLM cleanup
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    assert cleanup_response.status_code == 202
    cleanup_id = cleanup_response.json()["id"]

    # Step 6: Wait for cleanup to complete
    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id
    )
    assert cleaned_entry["cleaned_text"] is not None

    print(f"✓ Cleanup completed: {cleaned_entry['cleaned_text'][:80]}...")

    # Step 7: Verify we can retrieve everything
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200

    cleaned_list_response = await client.get(f"/api/v1/entries/{entry_id}/cleaned")
    assert cleaned_list_response.status_code == 200
    cleaned_list = cleaned_list_response.json()
    assert len(cleaned_list) >= 1

    print(f"\n✓ Complete workflow successful!")
    print(f"  Entry ID: {entry_id}")
    print(f"  Transcription ID: {transcription_id}")
    print(f"  Cleanup ID: {cleanup_id}")


@pytest.mark.asyncio
async def test_e2e_workflow_user_isolation(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    Test that users can't access each other's data throughout the workflow.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # User A: Register, login, upload
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_a_workflow@example.com", "password": "UserA123!"}
    )
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_a_workflow@example.com", "password": "UserA123!"}
    )
    token_a = login_a.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token_a}"

    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("user_a_file.mp3", f, "audio/mpeg")}
        upload_a = await client.post("/api/v1/upload", files=files)

    entry_a_id = upload_a.json()["id"]

    # Transcribe for User A
    transcribe_a = await client.post(
        f"/api/v1/entries/{entry_a_id}/transcribe",
        json={"language": "en"}
    )
    transcription_a_id = transcribe_a.json()["transcription_id"]

    # User B: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_b_workflow@example.com", "password": "UserB123!"}
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_b_workflow@example.com", "password": "UserB123!"}
    )
    token_b = login_b.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token_b}"

    # User B tries to access User A's resources
    entry_response = await client.get(f"/api/v1/entries/{entry_a_id}")
    assert entry_response.status_code == 404

    trans_response = await client.get(f"/api/v1/transcriptions/{transcription_a_id}")
    assert trans_response.status_code == 404

    # User B tries to trigger cleanup on User A's transcription
    # Should fail with either 400 (not completed) or 404 (not found)
    # Both are acceptable - the key is that User B cannot trigger cleanup
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_a_id}/cleanup"
    )
    assert cleanup_response.status_code in [400, 404], \
        f"Expected 400 or 404, got {cleanup_response.status_code}: {cleanup_response.json()}"
