"""
End-to-end tests for Notion integration (Phase 5).

These tests verify the complete Notion sync workflow works with REAL Notion API.
All tests use actual services (Whisper, Ollama, Notion) - no mocks.

Prerequisites:
- PostgreSQL database running
- Whisper model available
- Ollama running with llama3.2:3b model
- Notion API key set in NOTION_TEST_API_KEY env var
- Notion test database ID set in NOTION_TEST_DATABASE_ID env var

Run tests: pytest tests/test_e2e_notion.py -m e2e_real
Skip if services unavailable: pytest tests/test_e2e_notion.py
"""
import asyncio
import os
import pytest
from pathlib import Path
from httpx import AsyncClient
from typing import Tuple

from tests.e2e.e2e_utils import wait_for_transcription, wait_for_cleanup, poll_until_condition
from tests.conftest import app_is_available
from app.config import settings


def notion_test_available() -> bool:
    """Check if Notion test credentials are configured."""
    return (
        settings.NOTION_TEST_API_KEY is not None and
        settings.NOTION_TEST_DATABASE_ID is not None
    )


async def wait_for_notion_sync(
    client: AsyncClient,
    sync_id: str,
    max_wait: int = 60,
    poll_interval: int = 2
) -> dict:
    """
    Wait for a Notion sync to complete.

    Args:
        client: Authenticated HTTP client
        sync_id: UUID of the sync record
        max_wait: Maximum wait time in seconds
        poll_interval: Polling interval in seconds

    Returns:
        Completed sync data dict

    Raises:
        TimeoutError: If sync doesn't complete in time
        AssertionError: If sync fails
    """
    async def check_sync():
        response = await client.get(f"/api/v1/notion/sync/{sync_id}")
        sync_record = response.json()

        if sync_record["status"] == "failed":
            raise AssertionError(
                f"Notion sync failed: {sync_record.get('error_message', 'Unknown error')}"
            )

        is_complete = sync_record["status"] == "completed"
        return is_complete, sync_record

    return await poll_until_condition(
        check_fn=check_sync,
        max_wait_seconds=max_wait,
        poll_interval_seconds=poll_interval,
        operation_name="Notion sync"
    )


# ===== Real E2E Tests (Requires actual Notion API) =====

@pytest.mark.e2e_real
@pytest.mark.skipif(
    not (app_is_available() and notion_test_available()),
    reason="Required services not running or Notion test credentials not configured"
)
@pytest.mark.asyncio
async def test_e2e_real_full_workflow_with_notion_sync(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Real end-to-end test: Upload → Transcribe → Cleanup → Notion Sync

    This test uses REAL services:
    - Whisper for transcription
    - Ollama for cleanup
    - Notion API for sync

    Prerequisites:
    - Whisper model files
    - Ollama running: ollama serve
    - Model available: ollama pull llama3.2:3b
    - NOTION_TEST_API_KEY environment variable set
    - NOTION_TEST_DATABASE_ID environment variable set
    """
    client, email = authenticated_e2e_client

    notion_api_key = settings.NOTION_TEST_API_KEY
    notion_database_id = settings.NOTION_TEST_DATABASE_ID

    print(f"\n{'='*60}")
    print("REAL E2E TEST: Full Workflow with Notion Sync")
    print(f"{'='*60}")

    # Step 1: Configure Notion integration with REAL credentials
    print("\n[1/7] Configuring Notion integration...")
    config_response = await client.post(
        "/api/v1/notion/configure",
        json={
            "api_key": notion_api_key,
            "database_id": notion_database_id,
            "auto_sync": False  # Manual sync for testing
        }
    )
    assert config_response.status_code == 200, \
        f"Notion configuration failed: {config_response.json()}"
    config_data = config_response.json()
    print(f"✓ Connected to Notion database: {config_data['database_title']}")

    # Step 2: Upload real audio file
    print("\n[2/7] Uploading audio file...")
    audio_file = Path("tests/fixtures/crocodile.mp3")
    if not audio_file.exists():
        pytest.skip("Real audio file not found")

    with open(audio_file, 'rb') as f:
        files = {"file": ("dream_recording.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]
    print(f"✓ Audio uploaded: {entry_id}")

    # Step 3: Transcribe with real Whisper
    print("\n[3/7] Transcribing audio with Whisper...")
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )
    print(f"✓ Transcription completed")
    print(f"  Text: {transcription['transcribed_text'][:80]}...")

    # Step 4: Cleanup with real Ollama
    print("\n[4/7] Cleaning up text with LLM...")
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    assert cleanup_response.status_code == 202
    cleanup_id = cleanup_response.json()["id"]

    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id
    )
    print(f"✓ Cleanup completed")
    print(f"  Cleaned text: {cleaned_entry['cleaned_text'][:80]}...")

    # Step 5: Trigger Notion sync
    print("\n[5/7] Syncing to Notion...")
    sync_response = await client.post(f"/api/v1/notion/sync/{entry_id}")
    assert sync_response.status_code == 202
    sync_id = sync_response.json()["sync_id"]
    print(f"✓ Sync triggered: {sync_id}")

    # Step 6: Wait for sync to complete
    print("\n[6/7] Waiting for Notion sync to complete...")
    sync_record = await wait_for_notion_sync(
        client=client,
        sync_id=sync_id
    )
    assert sync_record["status"] == "completed"
    assert sync_record["notion_page_id"] is not None
    print(f"✓ Sync completed")
    print(f"  Notion Page ID: {sync_record['notion_page_id']}")
    if "notion_page_url" in sync_record and sync_record["notion_page_url"]:
        print(f"  Notion Page URL: {sync_record['notion_page_url']}")

    # Step 7: Verify sync record in list
    print("\n[7/7] Verifying sync record...")
    syncs_response = await client.get("/api/v1/notion/syncs")
    assert syncs_response.status_code == 200
    syncs_data = syncs_response.json()
    assert syncs_data["total"] >= 1

    # Find our sync in the list
    our_sync = next(
        (s for s in syncs_data["syncs"] if s["id"] == sync_id),
        None
    )
    assert our_sync is not None
    assert our_sync["status"] == "completed"
    print(f"✓ Sync record verified in list")

    print(f"\n{'='*60}")
    print("✅ FULL WORKFLOW WITH NOTION SYNC COMPLETED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Entry ID: {entry_id}")
    print(f"Transcription ID: {transcription_id}")
    print(f"Cleanup ID: {cleanup_id}")
    print(f"Sync ID: {sync_id}")
    print(f"Notion Page ID: {sync_record['notion_page_id']}")
    print(f"{'='*60}\n")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not (app_is_available() and notion_test_available()),
    reason="Required services not running or Notion test credentials not configured"
)
@pytest.mark.asyncio
async def test_e2e_real_auto_sync_workflow(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Real end-to-end test of AUTO-SYNC feature.

    Tests that cleanup completion automatically triggers Notion sync.
    """
    client, email = authenticated_e2e_client

    notion_api_key = settings.NOTION_TEST_API_KEY
    notion_database_id = settings.NOTION_TEST_DATABASE_ID

    print(f"\n{'='*60}")
    print("REAL E2E TEST: Auto-Sync Workflow")
    print(f"{'='*60}")

    # Step 1: Configure Notion with AUTO-SYNC enabled
    print("\n[1/5] Configuring Notion with auto-sync enabled...")
    config_response = await client.post(
        "/api/v1/notion/configure",
        json={
            "api_key": notion_api_key,
            "database_id": notion_database_id,
            "auto_sync": True  # Enable auto-sync
        }
    )
    assert config_response.status_code == 200
    print(f"✓ Auto-sync enabled")

    # Step 2: Upload audio
    print("\n[2/5] Uploading audio...")
    audio_file = Path("tests/fixtures/crocodile.mp3")
    if not audio_file.exists():
        pytest.skip("Real audio file not found")

    with open(audio_file, 'rb') as f:
        files = {"file": ("auto_sync_test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)
    entry_id = upload_response.json()["id"]
    print(f"✓ Audio uploaded: {entry_id}")

    # Step 3: Transcribe
    print("\n[3/5] Transcribing...")
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    transcription_id = transcribe_response.json()["transcription_id"]
    await wait_for_transcription(client=client, transcription_id=transcription_id)
    print(f"✓ Transcription completed")

    # Step 4: Trigger cleanup (should auto-trigger Notion sync)
    print("\n[4/5] Triggering cleanup (should auto-sync to Notion)...")
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    cleanup_id = cleanup_response.json()["id"]

    # Wait for cleanup to complete
    await wait_for_cleanup(client=client, cleanup_id=cleanup_id)
    print(f"✓ Cleanup completed")

    # Step 5: Check that Notion sync was automatically triggered
    print("\n[5/5] Verifying auto-sync was triggered...")
    # Give it a moment to trigger the background sync
    await asyncio.sleep(2)

    # Check sync list for this entry
    syncs_response = await client.get("/api/v1/notion/syncs?limit=10")
    assert syncs_response.status_code == 200
    syncs_data = syncs_response.json()

    # Find sync for our entry
    entry_syncs = [s for s in syncs_data["syncs"] if s["entry_id"] == entry_id]
    assert len(entry_syncs) >= 1, "Auto-sync should have created a sync record"

    sync_record = entry_syncs[0]
    print(f"✓ Auto-sync triggered: {sync_record['id']}")

    # Wait for auto-sync to complete
    if sync_record["status"] in ["pending", "processing"]:
        print("  Waiting for auto-sync to complete...")
        sync_record = await wait_for_notion_sync(
            client=client,
            sync_id=sync_record["id"]
        )

    assert sync_record["status"] == "completed"
    print(f"✓ Auto-sync completed")
    print(f"  Notion Page ID: {sync_record['notion_page_id']}")

    print(f"\n{'='*60}")
    print("✅ AUTO-SYNC WORKFLOW COMPLETED SUCCESSFULLY")
    print(f"{'='*60}\n")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not (app_is_available() and notion_test_available()),
    reason="Required services not running or Notion test credentials not configured"
)
@pytest.mark.asyncio
async def test_e2e_real_sync_update_workflow(
    authenticated_e2e_client: Tuple[AsyncClient, str]
):
    """
    Real end-to-end test of sync UPDATE (resync) functionality.

    Tests that re-syncing an entry updates the existing Notion page
    instead of creating a new one.
    """
    client, email = authenticated_e2e_client

    notion_api_key = settings.NOTION_TEST_API_KEY
    notion_database_id = settings.NOTION_TEST_DATABASE_ID

    print(f"\n{'='*60}")
    print("REAL E2E TEST: Sync Update (Resync) Workflow")
    print(f"{'='*60}")

    # Step 1: Configure Notion integration
    print("\n[1/8] Configuring Notion integration...")
    config_response = await client.post(
        "/api/v1/notion/configure",
        json={
            "api_key": notion_api_key,
            "database_id": notion_database_id,
            "auto_sync": False
        }
    )
    assert config_response.status_code == 200
    print(f"✓ Notion configured")

    # Step 2: Upload audio file
    print("\n[2/8] Uploading audio file...")
    audio_file = Path("tests/fixtures/crocodile.mp3")
    if not audio_file.exists():
        pytest.skip("Real audio file not found")

    with open(audio_file, 'rb') as f:
        files = {"file": ("resync_test.mp3", f, "audio/mpeg")}
        upload_response = await client.post("/api/v1/upload", files=files)

    assert upload_response.status_code == 201
    entry_id = upload_response.json()["id"]
    print(f"✓ Audio uploaded: {entry_id}")

    # Step 3: Transcribe
    print("\n[3/8] Transcribing audio...")
    transcribe_response = await client.post(
        f"/api/v1/entries/{entry_id}/transcribe",
        json={"language": "en"}
    )
    assert transcribe_response.status_code == 202
    transcription_id = transcribe_response.json()["transcription_id"]

    transcription = await wait_for_transcription(
        client=client,
        transcription_id=transcription_id
    )
    print(f"✓ Transcription completed")

    # Step 4: Initial cleanup
    print("\n[4/8] Running initial cleanup...")
    cleanup_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    assert cleanup_response.status_code == 202
    cleanup_id = cleanup_response.json()["id"]

    cleaned_entry = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup_id
    )
    print(f"✓ Initial cleanup completed")
    print(f"  Cleaned text: {cleaned_entry['cleaned_text'][:60]}...")

    # Step 5: First sync (creates new page)
    print("\n[5/8] First sync (should CREATE new Notion page)...")
    sync1_response = await client.post(f"/api/v1/notion/sync/{entry_id}")
    assert sync1_response.status_code == 202
    sync1_data = sync1_response.json()
    sync1_id = sync1_data["sync_id"]
    assert "will create" in sync1_data["message"].lower() or "create" in sync1_data["message"].lower()
    assert sync1_data["notion_page_id"] is None  # No existing page
    print(f"✓ First sync triggered: {sync1_id}")

    # Wait for first sync to complete
    print("  Waiting for first sync to complete...")
    sync1_record = await wait_for_notion_sync(
        client=client,
        sync_id=sync1_id
    )
    assert sync1_record["status"] == "completed"
    assert sync1_record["notion_page_id"] is not None
    first_page_id = sync1_record["notion_page_id"]
    print(f"✓ First sync completed - created page: {first_page_id}")

    # Step 6: Re-run cleanup (simulate user editing and re-cleaning)
    print("\n[6/8] Re-running cleanup (simulating content edit)...")
    cleanup2_response = await client.post(
        f"/api/v1/transcriptions/{transcription_id}/cleanup"
    )
    cleanup2_id = cleanup2_response.json()["id"]

    cleaned_entry2 = await wait_for_cleanup(
        client=client,
        cleanup_id=cleanup2_id
    )
    print(f"✓ Second cleanup completed")

    # Step 7: Second sync (should UPDATE existing page)
    print("\n[7/8] Second sync (should UPDATE existing Notion page)...")
    sync2_response = await client.post(f"/api/v1/notion/sync/{entry_id}")
    assert sync2_response.status_code == 202
    sync2_data = sync2_response.json()
    sync2_id = sync2_data["sync_id"]
    assert "will update" in sync2_data["message"].lower() or "update" in sync2_data["message"].lower()
    assert sync2_data["notion_page_id"] == first_page_id  # Should reference existing page
    print(f"✓ Second sync triggered: {sync2_id}")

    # Wait for second sync to complete
    print("  Waiting for second sync to complete...")
    sync2_record = await wait_for_notion_sync(
        client=client,
        sync_id=sync2_id
    )
    assert sync2_record["status"] == "completed"
    assert sync2_record["notion_page_id"] == first_page_id  # Should be SAME page ID
    print(f"✓ Second sync completed - updated same page: {sync2_record['notion_page_id']}")

    # Step 8: Verify only ONE page was created (not two)
    print("\n[8/8] Verifying sync records...")
    syncs_response = await client.get("/api/v1/notion/syncs")
    assert syncs_response.status_code == 200
    syncs_data = syncs_response.json()

    # Find all syncs for this entry
    entry_syncs = [s for s in syncs_data["syncs"] if s["entry_id"] == entry_id]
    assert len(entry_syncs) == 2, "Should have 2 sync records"

    # Both syncs should reference the SAME Notion page ID
    page_ids = [s["notion_page_id"] for s in entry_syncs if s["notion_page_id"]]
    assert len(set(page_ids)) == 1, "Both syncs should reference the same Notion page"
    assert page_ids[0] == first_page_id

    print(f"✓ Verified: Both syncs reference the same page")
    print(f"  Sync 1 (create): {sync1_id} → {first_page_id}")
    print(f"  Sync 2 (update): {sync2_id} → {first_page_id}")

    print(f"\n{'='*60}")
    print("✅ SYNC UPDATE WORKFLOW COMPLETED SUCCESSFULLY")
    print(f"{'='*60}")
    print(f"Entry ID: {entry_id}")
    print(f"First Sync ID: {sync1_id}")
    print(f"Second Sync ID: {sync2_id}")
    print(f"Notion Page ID (same for both): {first_page_id}")
    print(f"{'='*60}\n")
