"""
Integration tests for encrypted workflow.

Tests cover:
- Encrypted upload: all files are encrypted
- DEK creation: data encryption key created for encrypted entries
- Encryption is always enabled (no toggle)
"""

import uuid
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.voice_entry import VoiceEntry
from app.models.data_encryption_key import DataEncryptionKey


# =============================================================================
# Encrypted Upload Tests
# =============================================================================


class TestEncryptedUpload:
    """Tests for upload with encryption (always enabled)."""

    @pytest.mark.asyncio
    async def test_upload_encrypts_file(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Upload creates encrypted file (encryption is always enabled)."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post(
                "/api/v1/upload", files=files
            )

        assert response.status_code == 201
        data = response.json()
        entry_id = uuid.UUID(data["id"])

        # Verify entry is marked as encrypted in database
        entry = await db_session.get(VoiceEntry, entry_id)
        assert entry is not None
        assert entry.is_encrypted is True
        assert entry.file_path.endswith(".enc")
        assert entry.encryption_version == "local-v1"

    @pytest.mark.asyncio
    async def test_dek_created_for_entry(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """DEK is created when encrypting a voice entry."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post(
                "/api/v1/upload", files=files
            )

        assert response.status_code == 201
        entry_id = uuid.UUID(response.json()["id"])

        # Verify DEK was created
        stmt = select(DataEncryptionKey).where(
            DataEncryptionKey.voice_entry_id == entry_id,
            DataEncryptionKey.user_id == test_user.id,
        )
        result = await db_session.execute(stmt)
        dek = result.scalar_one_or_none()

        assert dek is not None
        assert dek.voice_entry_id == entry_id
        assert dek.user_id == test_user.id
        assert dek.encrypted_dek is not None
        assert len(dek.encrypted_dek) > 0


# =============================================================================
# Upload and Transcribe Tests
# =============================================================================


class TestEncryptedUploadAndTranscribe:
    """Tests for upload-and-transcribe with encryption."""

    @pytest.mark.asyncio
    async def test_upload_and_transcribe_encrypts_file(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Upload-and-transcribe creates encrypted file."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post(
                "/api/v1/upload-and-transcribe",
                files=files,
                data={"entry_type": "dream", "language": "en"},
            )

        assert response.status_code == 202
        data = response.json()
        entry_id = uuid.UUID(data["entry_id"])

        # Verify entry is marked as encrypted
        entry = await db_session.get(VoiceEntry, entry_id)
        assert entry is not None
        assert entry.is_encrypted is True
        assert entry.file_path.endswith(".enc")


# =============================================================================
# Complete Workflow Tests
# =============================================================================


class TestEncryptedCompleteWorkflow:
    """Tests for complete workflow (upload-transcribe-cleanup) with encryption."""

    @pytest.mark.asyncio
    async def test_complete_workflow_encrypts_file(
        self,
        authenticated_client: AsyncClient,
        sample_mp3_path: Path,
        db_session: AsyncSession,
        test_user: User,
    ):
        """Complete workflow creates encrypted file."""
        with open(sample_mp3_path, "rb") as f:
            files = {"file": ("test_audio.mp3", f, "audio/mpeg")}
            response = await authenticated_client.post(
                "/api/v1/upload-transcribe-cleanup",
                files=files,
                data={"entry_type": "dream", "language": "en"},
            )

        assert response.status_code == 202
        data = response.json()
        entry_id = uuid.UUID(data["entry_id"])

        # Verify entry is marked as encrypted
        entry = await db_session.get(VoiceEntry, entry_id)
        assert entry is not None
        assert entry.is_encrypted is True
        assert entry.file_path.endswith(".enc")

        # Verify DEK was created
        stmt = select(DataEncryptionKey).where(
            DataEncryptionKey.voice_entry_id == entry_id
        )
        result = await db_session.execute(stmt)
        dek = result.scalar_one_or_none()
        assert dek is not None
