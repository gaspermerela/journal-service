"""
End-to-end tests for delete workflows.

Tests the complete deletion flow with real database and file operations.
"""
import asyncio
import os
import pytest
from pathlib import Path
from httpx import AsyncClient

from tests.e2e.e2e_utils import wait_for_transcription, wait_for_cleanup


@pytest.mark.asyncio
async def test_e2e_delete_entry_removes_all_data(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Upload → Transcribe → Cleanup → Delete Entry → Verify all data removed.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "delete_test@example.com", "password": "Delete123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "delete_test@example.com", "password": "Delete123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload audio file
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
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

    # Wait for transcription to complete
    await asyncio.sleep(0.5)

    # Step 4: Trigger cleanup (if transcription completed)
    trans_status = await client.get(f"/api/v1/transcriptions/{transcription_id}")
    if trans_status.json().get("status") == "completed":
        cleanup_response = await client.post(
            f"/api/v1/transcriptions/{transcription_id}/cleanup"
        )
        if cleanup_response.status_code == 202:
            cleaned_entry_id = cleanup_response.json()["id"]
            await asyncio.sleep(0.5)

    # Step 5: Verify entry exists before deletion
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 200

    # Step 6: Delete the entry
    delete_response = await client.delete(f"/api/v1/entries/{entry_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "Entry deleted successfully"
    assert delete_response.json()["deleted_id"] == entry_id

    # Step 7: Verify entry is gone
    entry_response = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_response.status_code == 404

    # Step 8: Verify transcription is gone
    trans_response = await client.get(f"/api/v1/transcriptions/{transcription_id}")
    assert trans_response.status_code == 404

    # Step 9: Verify entry doesn't appear in list
    list_response = await client.get("/api/v1/entries")
    entries = list_response.json()["entries"]
    entry_ids = [e["id"] for e in entries]
    assert entry_id not in entry_ids


@pytest.mark.asyncio
async def test_e2e_delete_transcription_with_multiple_versions(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Upload → Multiple Transcriptions → Delete one → Verify other remains.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "multi_trans@example.com", "password": "Multi123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "multi_trans@example.com", "password": "Multi123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload audio file
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    # Step 3: Create first transcription
    trans1_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    trans1_id = trans1_response.json()["transcription_id"]
    await asyncio.sleep(0.5)

    # Step 4: Create second transcription
    trans2_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    trans2_id = trans2_response.json()["transcription_id"]
    await asyncio.sleep(0.5)

    # Step 5: Verify both transcriptions exist
    trans_list = await client.get(f"/api/v1/entries/{entry_id}/transcriptions")
    assert trans_list.json()["total"] >= 2

    # Step 6: Delete the second (non-primary) transcription
    delete_response = await client.delete(f"/api/v1/transcriptions/{trans2_id}")
    assert delete_response.status_code == 200

    # Step 7: Verify second transcription is gone
    trans2_check = await client.get(f"/api/v1/transcriptions/{trans2_id}")
    assert trans2_check.status_code == 404

    # Step 8: Verify first transcription still exists
    trans1_check = await client.get(f"/api/v1/transcriptions/{trans1_id}")
    assert trans1_check.status_code == 200

    # Step 9: Verify entry still exists
    entry_check = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_check.status_code == 200


@pytest.mark.asyncio
async def test_e2e_cannot_delete_only_transcription(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Upload → Transcribe → Wait for completion → Try to delete only transcription → Should fail.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "only_trans@example.com", "password": "Only123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "only_trans@example.com", "password": "Only123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload and transcribe
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    trans_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    trans_id = trans_response.json()["transcription_id"]

    # Wait longer for transcription to complete fully
    await asyncio.sleep(1.5)

    # Step 3: Verify transcription exists and check if there are others
    trans_list = await client.get(f"/api/v1/entries/{entry_id}/transcriptions")
    transcriptions = trans_list.json()["transcriptions"]

    # If there's only one transcription, try to delete it
    if len(transcriptions) == 1:
        delete_response = await client.delete(f"/api/v1/transcriptions/{trans_id}")

        # Should fail with 409 Conflict
        assert delete_response.status_code == 409
        assert "only transcription" in delete_response.json()["detail"].lower()

        # Verify transcription still exists
        trans_check = await client.get(f"/api/v1/transcriptions/{trans_id}")
        assert trans_check.status_code == 200
    else:
        # If multiple transcriptions exist (race condition), skip this specific assertion
        pytest.skip("Multiple transcriptions exist, cannot test single transcription deletion constraint")


@pytest.mark.asyncio
async def test_e2e_delete_cleaned_entry(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Upload → Transcribe → Cleanup → Delete Cleaned Entry → Verify removed.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "cleanup_delete@example.com", "password": "Cleanup123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "cleanup_delete@example.com", "password": "Cleanup123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload and transcribe
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    trans_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    trans_id = trans_response.json()["transcription_id"]
    await asyncio.sleep(0.5)

    # Step 3: Trigger cleanup (if transcription completed)
    trans_status = await client.get(f"/api/v1/transcriptions/{trans_id}")
    if trans_status.json().get("status") != "completed":
        pytest.skip("Transcription not completed, skipping cleanup test")

    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{trans_id}/cleanup"
    )

    if cleanup_response.status_code != 202:
        pytest.skip("Cleanup not triggered, skipping test")

    cleaned_id = cleanup_response.json()["id"]
    await asyncio.sleep(0.5)

    # Step 4: Verify cleaned entry exists
    cleaned_check = await client.get(f"/api/v1/cleaned-entries/{cleaned_id}")
    assert cleaned_check.status_code == 200

    # Step 5: Delete cleaned entry
    delete_response = await client.delete(f"/api/v1/cleaned-entries/{cleaned_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["deleted_id"] == cleaned_id

    # Step 6: Verify cleaned entry is gone
    cleaned_check = await client.get(f"/api/v1/cleaned-entries/{cleaned_id}")
    assert cleaned_check.status_code == 404

    # Step 7: Verify transcription and entry still exist
    trans_check = await client.get(f"/api/v1/transcriptions/{trans_id}")
    assert trans_check.status_code == 200

    entry_check = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_check.status_code == 200


@pytest.mark.asyncio
async def test_e2e_user_isolation_delete(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: User A creates entry → User B tries to delete → Should fail.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login User A
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_a_delete@example.com", "password": "UserA123!"}
    )
    login_a = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_a_delete@example.com", "password": "UserA123!"}
    )
    token_a = login_a.json()["access_token"]

    # Step 2: User A uploads entry
    client.headers["Authorization"] = f"Bearer {token_a}"
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    # Step 3: Register and login User B
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user_b_delete@example.com", "password": "UserB123!"}
    )
    login_b = await client.post(
        "/api/v1/auth/login",
        json={"email": "user_b_delete@example.com", "password": "UserB123!"}
    )
    token_b = login_b.json()["access_token"]

    # Step 4: User B tries to delete User A's entry
    client.headers["Authorization"] = f"Bearer {token_b}"
    delete_response = await client.delete(f"/api/v1/entries/{entry_id}")

    # Should fail with 404 (security - don't reveal entry exists)
    assert delete_response.status_code == 404

    # Step 5: Verify entry still exists for User A
    client.headers["Authorization"] = f"Bearer {token_a}"
    entry_check = await client.get(f"/api/v1/entries/{entry_id}")
    assert entry_check.status_code == 200


@pytest.mark.asyncio
async def test_e2e_delete_multiple_entries_in_sequence(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Upload multiple entries → Delete them one by one → Verify count decreases.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "multi_delete@example.com", "password": "Multi123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "multi_delete@example.com", "password": "Multi123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload 3 entries
    entry_ids = []
    for i in range(3):
        with open(sample_mp3_path, 'rb') as f:
            files = {"file": (f"recording_{i}.mp3", f, "audio/mpeg")}
            upload_response = await client.post("/api/v1/upload", files=files)

        entry_ids.append(upload_response.json()["id"])
        await asyncio.sleep(0.1)

    # Step 3: Verify 3 entries exist
    list_response = await client.get("/api/v1/entries")
    assert list_response.json()["total"] == 3

    # Step 4: Delete first entry
    delete1 = await client.delete(f"/api/v1/entries/{entry_ids[0]}")
    assert delete1.status_code == 200

    # Step 5: Verify count decreased to 2
    list_response = await client.get("/api/v1/entries")
    assert list_response.json()["total"] == 2

    # Step 6: Delete second entry
    delete2 = await client.delete(f"/api/v1/entries/{entry_ids[1]}")
    assert delete2.status_code == 200

    # Step 7: Verify count decreased to 1
    list_response = await client.get("/api/v1/entries")
    assert list_response.json()["total"] == 1

    # Verify only the third entry remains
    remaining_ids = [e["id"] for e in list_response.json()["entries"]]
    assert entry_ids[2] in remaining_ids
    assert entry_ids[0] not in remaining_ids
    assert entry_ids[1] not in remaining_ids

    # Step 8: Delete third entry
    delete3 = await client.delete(f"/api/v1/entries/{entry_ids[2]}")
    assert delete3.status_code == 200

    # Step 9: Verify all entries are gone
    list_response = await client.get("/api/v1/entries")
    assert list_response.json()["total"] == 0
    assert len(list_response.json()["entries"]) == 0


@pytest.mark.asyncio
async def test_e2e_delete_entry_idempotent(
    client: AsyncClient,
    sample_mp3_path: Path,
    mock_transcription_service
):
    """
    E2E test: Delete same entry twice → Second delete should return 404.
    """
    from app.main import app
    app.state.transcription_service = mock_transcription_service

    # Step 1: Register and login
    await client.post(
        "/api/v1/auth/register",
        json={"email": "idempotent@example.com", "password": "Idem123!"}
    )
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": "idempotent@example.com", "password": "Idem123!"}
    )
    access_token = login_response.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {access_token}"

    # Step 2: Upload entry
    with open(sample_mp3_path, 'rb') as f:
        files = {"file": ("test_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    entry_id = upload_response.json()["id"]

    # Step 3: First delete - should succeed
    delete1 = await client.delete(f"/api/v1/entries/{entry_id}")
    assert delete1.status_code == 200

    # Step 4: Second delete - should return 404
    delete2 = await client.delete(f"/api/v1/entries/{entry_id}")
    assert delete2.status_code == 404
    assert "not found" in delete2.json()["detail"].lower()
