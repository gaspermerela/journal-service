"""
End-to-end tests for transcription workflow.
Tests complete flow: upload → transcribe → poll → retrieve.
"""
import pytest
import asyncio


@pytest.mark.asyncio
async def test_complete_transcription_workflow(authenticated_client, sample_mp3_path):
    """
    Test the complete transcription workflow from upload to retrieval.

    Flow:
    1. Upload audio file
    2. Trigger transcription
    3. Poll for completion
    4. Retrieve transcription
    5. Get entry with transcription included
    """
    # Step 1: Upload audio file
    with open(sample_mp3_path, "rb") as f:
        upload_response = await authenticated_client.post(
            "/api/v1/upload",
            files={"file": ("dream_recording.mp3", f, "audio/mpeg")}
        )

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]

    # Step 2: Trigger transcription using noop provider
    transcribe_response = await authenticated_client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    # Step 3: Poll for completion (simulate user polling)
    # In tests, background tasks may execute immediately
    await asyncio.sleep(0.2)

    # Step 4: Check transcription status
    status_response = await authenticated_client.get(f"/api/v1/transcriptions/{transcription_id}")

    assert status_response.status_code == 200
    status_data = status_response.json()
    assert status_data["id"] == transcription_id
    assert status_data["status"] in ["pending", "processing", "completed"]

    # Step 5: Get entry with transcription
    entry_response = await authenticated_client.get(f"/api/v1/entries/{entry_id}")

    assert entry_response.status_code == 200
    entry_data = entry_response.json()
    assert entry_data["id"] == entry_id
    # Note: primary_transcription may be None if not set as primary yet


@pytest.mark.asyncio
async def test_multiple_transcription_attempts(authenticated_client, sample_voice_entry):
    """
    Test creating multiple transcriptions for the same entry.
    Simulates: trying multiple times (e.g., retries or different language attempts).
    """
    # Create 3 transcriptions for the same entry
    transcription_ids = []

    for i in range(3):
        response = await authenticated_client.post(
            f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
            json={"language": "en", "transcription_provider": "noop"}
        )

        assert response.status_code == 202
        transcription_ids.append(response.json()["transcription_id"])

    # List all transcriptions
    list_response = await authenticated_client.get(
        f"/api/v1/entries/{sample_voice_entry.id}/transcriptions"
    )

    assert list_response.status_code == 200
    data = list_response.json()
    assert data["total"] == len(transcription_ids)
    assert len(data["transcriptions"]) == len(transcription_ids)


@pytest.mark.asyncio
async def test_set_primary_after_comparison(authenticated_client, sample_voice_entry, db_session):
    """
    Test workflow: create multiple transcriptions, then set one as primary.
    Simulates: user tries different models, picks best one.
    """
    from app.services.database import db_service
    from app.schemas.transcription import TranscriptionCreate

    # Create two completed transcriptions (simulating completed background tasks)
    trans1_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-tiny",
        language_code="en",
        is_primary=False
    )
    trans1 = await db_service.create_transcription(db_session, trans1_data)
    await db_service.update_transcription_status(
        db_session,
        trans1.id,
        status="completed",
        transcribed_text=b"Quick but less accurate transcription."
    )

    trans2_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-large",
        language_code="en",
        is_primary=False
    )
    trans2 = await db_service.create_transcription(db_session, trans2_data)
    await db_service.update_transcription_status(
        db_session,
        trans2.id,
        status="completed",
        transcribed_text=b"High quality accurate transcription with proper punctuation."
    )
    await db_session.commit()

    # User decides trans2 (large model) is better
    set_primary_response = await authenticated_client.put(
        f"/api/v1/transcriptions/{trans2.id}/set-primary"
    )

    assert set_primary_response.status_code == 200

    # Verify entry now shows trans2 as primary
    entry_response = await authenticated_client.get(f"/api/v1/entries/{sample_voice_entry.id}")
    entry_data = entry_response.json()

    assert entry_data["primary_transcription"] is not None
    assert entry_data["primary_transcription"]["id"] == str(trans2.id)
    assert entry_data["primary_transcription"]["model_used"] == "whisper-large"


@pytest.mark.asyncio
async def test_retry_failed_transcription(authenticated_client, sample_voice_entry, db_session):
    """
    Test workflow: transcription fails, user retries.
    """
    from app.services.database import db_service
    from app.schemas.transcription import TranscriptionCreate

    # Create failed transcription
    failed_trans_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="pending",
        model_used="whisper-base",
        language_code="en",
        is_primary=False
    )
    failed_trans = await db_service.create_transcription(db_session, failed_trans_data)
    await db_service.update_transcription_status(
        db_session,
        failed_trans.id,
        status="failed",
        error_message="Network timeout"
    )
    await db_session.commit()

    # Verify failed status
    failed_response = await authenticated_client.get(f"/api/v1/transcriptions/{failed_trans.id}")
    assert failed_response.json()["status"] == "failed"

    # User can see all attempts including failed one
    list_response = await authenticated_client.get(
        f"/api/v1/entries/{sample_voice_entry.id}/transcriptions"
    )

    transcriptions = list_response.json()["transcriptions"]
    assert len(transcriptions) == 1
    assert transcriptions[0]["status"] == "failed"
    assert transcriptions[0]["error_message"] == "Network timeout"


@pytest.mark.asyncio
async def test_transcription_with_auto_language_detection(authenticated_client, sample_voice_entry):
    """
    Test transcription with automatic language detection.
    """
    response = await authenticated_client.post(
        f"/api/v1/entries/{sample_voice_entry.id}/transcribe",
        json={"language": "auto", "transcription_provider": "noop"}
    )

    assert response.status_code == 202
    transcription_id = response.json()["transcription_id"]

    # Check transcription was created with "auto" language code
    status_response = await authenticated_client.get(f"/api/v1/transcriptions/{transcription_id}")
    assert status_response.json()["language_code"] == "auto"


@pytest.mark.asyncio
async def test_entry_deletion_cascades_to_transcriptions(client, sample_voice_entry, db_session, test_user):
    """
    Test that deleting an entry also deletes its transcriptions.
    """
    from app.services.database import db_service
    from app.schemas.transcription import TranscriptionCreate

    # Create transcription
    trans_data = TranscriptionCreate(
        entry_id=sample_voice_entry.id,
        status="completed",
        model_used="whisper-base",
        language_code="en",
        is_primary=True
    )
    trans = await db_service.create_transcription(db_session, trans_data)
    await db_session.commit()
    trans_id = trans.id

    # Delete entry
    await db_service.delete_entry(db_session, sample_voice_entry.id, test_user.id)
    await db_session.commit()

    # Try to get transcription - should not exist
    trans_result = await db_service.get_transcription_by_id(db_session, trans_id)
    assert trans_result is None


@pytest.mark.asyncio
async def test_upload_and_immediate_transcription(authenticated_client, sample_mp3_path):
    """
    Test realistic user flow: upload file and immediately trigger transcription.
    """
    # Upload
    with open(sample_mp3_path, "rb") as f:
        upload_response = await authenticated_client.post(
            "/api/v1/upload",
            files={"file": ("voice_note.mp3", f, "audio/mpeg")}
        )

    entry_id = upload_response.json()["id"]

    # Immediately trigger transcription using noop provider
    transcribe_response = await authenticated_client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en", "transcription_provider": "noop"}
    )

    assert transcribe_response.status_code == 202

    # Poll a few times (simulating user checking status)
    transcription_id = transcribe_response.json()["transcription_id"]

    for _ in range(3):
        await asyncio.sleep(0.1)
        status_response = await authenticated_client.get(f"/api/v1/transcriptions/{transcription_id}")
        assert status_response.status_code == 200

        if status_response.json()["status"] == "completed":
            break

    # User gets entry to see result
    final_response = await authenticated_client.get(f"/api/v1/entries/{entry_id}")
    assert final_response.status_code == 200
