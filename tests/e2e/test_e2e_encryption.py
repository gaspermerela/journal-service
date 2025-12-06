"""
End-to-end tests for encrypted workflow.

Tests cover the full encrypted workflow with real services:
- Upload → Transcribe → Cleanup with encryption (always enabled)
- Audio download with decryption
- Multiple users each with encrypted entries

IMPORTANT: These tests require:
- Running backend with encryption service configured
- Environment variables set (GROQ_API_KEY, etc.)
- Run manually: pytest tests/e2e/test_e2e_encryption.py -v -m e2e_real

DO NOT RUN AUTOMATICALLY IN CI/CD.
"""

import asyncio
import os
from pathlib import Path
from typing import AsyncGenerator, Tuple

import pytest
from httpx import AsyncClient

from tests.conftest import (
    E2E_TRANSCRIPTION_TIMEOUT,
    E2E_CLEANUP_TIMEOUT,
    app_is_available,
)


# =============================================================================
# E2E Fixtures
# =============================================================================


@pytest.fixture
async def e2e_encryption_client() -> AsyncGenerator[Tuple[AsyncClient, str], None]:
    """
    Create a new user, authenticate, and return client.

    This fixture creates a real HTTP client that connects to the running backend.
    Encryption is always enabled for all users.

    Returns:
        Tuple of (authenticated client, user email)
    """
    async with AsyncClient(
        base_url="http://localhost:8000", timeout=120.0
    ) as client:
        # Generate unique email for this test
        email = f"e2e_encryption_{os.urandom(4).hex()}@example.com"
        password = "E2EEncryptionPassword123!"

        # Register
        register_response = await client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        assert register_response.status_code == 201, f"Registration failed: {register_response.text}"

        # Login
        login_response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"

        # Set authorization header
        access_token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {access_token}"

        yield client, email


@pytest.fixture
async def e2e_second_user_client() -> AsyncGenerator[Tuple[AsyncClient, str], None]:
    """
    Create a second user for multi-user tests.

    Returns:
        Tuple of (authenticated client, user email)
    """
    async with AsyncClient(
        base_url="http://localhost:8000", timeout=120.0
    ) as client:
        # Generate unique email for this test
        email = f"e2e_second_user_{os.urandom(4).hex()}@example.com"
        password = "E2ESecondUserPassword123!"

        # Register
        register_response = await client.post(
            "/api/v1/auth/register", json={"email": email, "password": password}
        )
        assert register_response.status_code == 201

        # Login
        login_response = await client.post(
            "/api/v1/auth/login", json={"email": email, "password": password}
        )
        assert login_response.status_code == 200

        # Set authorization header
        access_token = login_response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {access_token}"

        yield client, email


# =============================================================================
# E2E Tests - Full Encrypted Workflow
# =============================================================================


@pytest.mark.e2e_real
@pytest.mark.asyncio
async def test_e2e_full_encrypted_workflow(
    e2e_encryption_client: Tuple[AsyncClient, str],
    real_audio_mp3_path: Path,
):
    """
    E2E test: Upload → Transcribe → Cleanup with encryption.

    Tests the complete workflow:
    1. Upload audio file (always encrypted)
    2. Transcription processes encrypted audio
    3. Cleanup processes encrypted transcription
    4. Retrieve cleaned entry (should be decrypted)
    """
    if not app_is_available():
        pytest.skip("Backend not available at http://localhost:8000")

    client, email = e2e_encryption_client

    # Upload + transcribe + cleanup
    with open(real_audio_mp3_path, "rb") as f:
        files = {"file": ("test_e2e_encrypted.mp3", f, "audio/mpeg")}
        response = await client.post(
            "/api/v1/upload-transcribe-cleanup",
            files=files,
            data={"entry_type": "dream", "language": "en"},
        )

    assert response.status_code == 202, f"Upload failed: {response.text}"
    data = response.json()

    entry_id = data["entry_id"]
    transcription_id = data["transcription_id"]
    cleanup_id = data["cleanup_id"]

    # Wait for transcription to complete
    for _ in range(E2E_TRANSCRIPTION_TIMEOUT):
        trans_response = await client.get(f"/api/v1/transcriptions/{transcription_id}")
        assert trans_response.status_code == 200
        trans_data = trans_response.json()

        if trans_data["status"] == "completed":
            break
        if trans_data["status"] == "failed":
            pytest.fail(f"Transcription failed: {trans_data.get('error_message')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Transcription timed out")

    # Verify transcription text is available (decrypted)
    assert trans_data["transcribed_text"] is not None
    assert len(trans_data["transcribed_text"]) > 0

    # Wait for cleanup to complete
    for _ in range(E2E_CLEANUP_TIMEOUT):
        cleanup_response = await client.get(f"/api/v1/cleaned-entries/{cleanup_id}")
        assert cleanup_response.status_code == 200
        cleanup_data = cleanup_response.json()

        if cleanup_data["status"] == "completed":
            break
        if cleanup_data["status"] == "failed":
            pytest.fail(f"Cleanup failed: {cleanup_data.get('error_message')}")

        await asyncio.sleep(1)
    else:
        pytest.fail("Cleanup timed out")

    # Verify cleaned text is available (decrypted)
    assert cleanup_data["cleaned_text"] is not None
    assert len(cleanup_data["cleaned_text"]) > 0


@pytest.mark.e2e_real
@pytest.mark.asyncio
async def test_e2e_encrypted_audio_download(
    e2e_encryption_client: Tuple[AsyncClient, str],
    real_audio_mp3_path: Path,
):
    """
    E2E test: Download encrypted audio file.

    Verifies that:
    1. Audio is uploaded and encrypted
    2. Download endpoint transparently decrypts the audio
    3. Downloaded audio is playable/valid
    """
    if not app_is_available():
        pytest.skip("Backend not available at http://localhost:8000")

    client, email = e2e_encryption_client

    # Upload audio file
    with open(real_audio_mp3_path, "rb") as f:
        files = {"file": ("test_download.mp3", f, "audio/mpeg")}
        response = await client.post("/api/v1/upload", files=files)

    assert response.status_code == 201
    entry_id = response.json()["id"]

    # Download the audio (should be decrypted transparently)
    download_response = await client.get(f"/api/v1/entries/{entry_id}/audio")
    assert download_response.status_code == 200

    # Verify we got audio content
    audio_content = download_response.content
    assert len(audio_content) > 0

    # Verify it's valid audio - could be WAV or MP3 depending on preprocessing
    # WAV files start with "RIFF", MP3 files start with 0xFF 0xFB (frame sync)
    is_wav = audio_content[:4] == b"RIFF"
    is_mp3 = audio_content[:2] == b"\xff\xfb" or audio_content[:3] == b"ID3"
    assert is_wav or is_mp3, f"Unknown audio format, first bytes: {audio_content[:4]}"


@pytest.mark.e2e_real
@pytest.mark.asyncio
async def test_e2e_multiple_encrypted_users(
    e2e_encryption_client: Tuple[AsyncClient, str],
    e2e_second_user_client: Tuple[AsyncClient, str],
    real_audio_mp3_path: Path,
):
    """
    E2E test: Multiple users each with encrypted entries.

    Tests that:
    1. User A creates encrypted entries
    2. User B creates encrypted entries
    3. Each user can only access their own entries
    """
    if not app_is_available():
        pytest.skip("Backend not available at http://localhost:8000")

    client_a, email_a = e2e_encryption_client
    client_b, email_b = e2e_second_user_client

    # User A uploads
    with open(real_audio_mp3_path, "rb") as f:
        files = {"file": ("user_a.mp3", f, "audio/mpeg")}
        response_a = await client_a.post("/api/v1/upload", files=files)

    assert response_a.status_code == 201
    entry_a_id = response_a.json()["id"]

    # User B uploads
    with open(real_audio_mp3_path, "rb") as f:
        files = {"file": ("user_b.mp3", f, "audio/mpeg")}
        response_b = await client_b.post("/api/v1/upload", files=files)

    assert response_b.status_code == 201
    entry_b_id = response_b.json()["id"]

    # User A can access their entry
    response = await client_a.get(f"/api/v1/entries/{entry_a_id}")
    assert response.status_code == 200

    # User A cannot access User B's entry
    response = await client_a.get(f"/api/v1/entries/{entry_b_id}")
    assert response.status_code == 404

    # User B can access their entry
    response = await client_b.get(f"/api/v1/entries/{entry_b_id}")
    assert response.status_code == 200

    # User B cannot access User A's entry
    response = await client_b.get(f"/api/v1/entries/{entry_a_id}")
    assert response.status_code == 404

    # Both users can download their own encrypted audio
    download_a = await client_a.get(f"/api/v1/entries/{entry_a_id}/audio")
    assert download_a.status_code == 200
    assert len(download_a.content) > 0

    download_b = await client_b.get(f"/api/v1/entries/{entry_b_id}/audio")
    assert download_b.status_code == 200
    assert len(download_b.content) > 0
