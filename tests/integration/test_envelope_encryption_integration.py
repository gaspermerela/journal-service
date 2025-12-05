"""
Integration tests for envelope encryption service.

Tests cover:
- EnvelopeEncryptionService: DEK management, data/file encryption, GDPR deletion
- Multi-user isolation: different users can't access each other's DEKs
- File encryption/decryption
- One DEK per VoiceEntry design
"""

import os
import uuid
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.voice_entry import VoiceEntry
from app.services.encryption_providers.local_kek import LocalKEKProvider
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    DEKNotFoundError,
    DEKDestroyedError,
)


# =============================================================================
# Helper to create VoiceEntry
# =============================================================================


async def create_voice_entry(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    tmp_path: Path = None,
) -> VoiceEntry:
    """Create a VoiceEntry for testing encryption."""
    entry_id = uuid.uuid4()
    saved_filename = f"{entry_id}_test.mp3"
    file_path = str(tmp_path / saved_filename) if tmp_path else f"/tmp/{saved_filename}"

    entry = VoiceEntry(
        id=entry_id,
        user_id=user_id,
        original_filename="test.mp3",
        saved_filename=saved_filename,
        file_path=file_path,
        duration_seconds=60.0,
    )
    db_session.add(entry)
    await db_session.flush()
    return entry


# =============================================================================
# EnvelopeEncryptionService Integration Tests (with DB)
# =============================================================================


class TestEnvelopeEncryptionServiceIntegration:
    """Integration tests for EnvelopeEncryptionService with database."""

    @pytest.fixture
    def encryption_service(self) -> EnvelopeEncryptionService:
        """Create encryption service with local provider."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        return EnvelopeEncryptionService(provider)

    @pytest.mark.asyncio
    async def test_create_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Creates DEK and stores in database."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        dek_id = await encryption_service.create_dek(
            db_session,
            user_id=test_user.id,
            voice_entry_id=voice_entry.id,
        )

        assert dek_id is not None

        # Verify DEK is in database
        dek_record = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert dek_record is not None
        assert dek_record.user_id == test_user.id
        assert dek_record.voice_entry_id == voice_entry.id
        assert dek_record.encryption_version == "local-v1"
        assert not dek_record.is_deleted

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_data_roundtrip(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Data encrypts and decrypts correctly through full service."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        original_data = "This is my secret dream journal entry."

        # Encrypt
        encrypted = await encryption_service.encrypt_data(
            db_session,
            data=original_data,
            voice_entry_id=voice_entry.id,
            user_id=test_user.id,
        )

        assert encrypted != original_data.encode()
        assert len(encrypted) > len(original_data)

        # Decrypt
        decrypted = await encryption_service.decrypt_data(
            db_session,
            encrypted_data=encrypted,
            voice_entry_id=voice_entry.id,
            user_id=test_user.id,
        )

        assert decrypted.decode("utf-8") == original_data

    @pytest.mark.asyncio
    async def test_encrypt_data_creates_dek_automatically(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Encrypting data for new VoiceEntry creates DEK automatically."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # No DEK exists yet
        assert await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        ) is None

        # Encrypt - should create DEK
        await encryption_service.encrypt_data(
            db_session,
            data="secret data",
            voice_entry_id=voice_entry.id,
            user_id=test_user.id,
        )

        # DEK should now exist
        dek = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert dek is not None

    @pytest.mark.asyncio
    async def test_encrypt_reuses_existing_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Multiple encryptions for same VoiceEntry use same DEK."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # First encryption creates DEK
        await encryption_service.encrypt_data(
            db_session, "data 1", voice_entry.id, test_user.id
        )
        dek_1 = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )

        # Second encryption reuses DEK
        await encryption_service.encrypt_data(
            db_session, "data 2", voice_entry.id, test_user.id
        )
        dek_2 = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )

        assert dek_1.id == dek_2.id

    @pytest.mark.asyncio
    async def test_destroy_dek_gdpr_deletion(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Destroying DEK makes data permanently unrecoverable."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Encrypt some data
        encrypted = await encryption_service.encrypt_data(
            db_session, "secret data", voice_entry.id, test_user.id
        )

        # Verify we can decrypt
        decrypted = await encryption_service.decrypt_data(
            db_session, encrypted, voice_entry.id, test_user.id
        )
        assert decrypted.decode() == "secret data"

        # Destroy DEK (GDPR deletion)
        destroyed = await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert destroyed is True

        # DEK record should be marked as deleted
        dek = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert dek.is_deleted
        assert dek.deleted_at is not None

        # Attempting to decrypt should fail
        with pytest.raises(DEKDestroyedError, match="has been destroyed"):
            await encryption_service.decrypt_data(
                db_session, encrypted, voice_entry.id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_destroy_dek_returns_false_if_not_found(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Destroying nonexistent DEK returns False."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        result = await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_encrypt_after_destroy_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Cannot encrypt new data after DEK is destroyed."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Create and destroy DEK
        await encryption_service.encrypt_data(
            db_session, "data", voice_entry.id, test_user.id
        )
        await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )

        # Attempting to encrypt should fail
        with pytest.raises(DEKDestroyedError, match="has been destroyed"):
            await encryption_service.encrypt_data(
                db_session, "new data", voice_entry.id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_decrypt_nonexistent_dek_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Decrypting data with no DEK fails."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        fake_encrypted = os.urandom(50)

        with pytest.raises(DEKNotFoundError, match="No DEK found"):
            await encryption_service.decrypt_data(
                db_session, fake_encrypted, voice_entry.id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_encrypt_empty_data_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Encrypting empty data raises ValueError."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        with pytest.raises(ValueError, match="cannot be empty"):
            await encryption_service.encrypt_data(
                db_session, "", voice_entry.id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_decrypt_empty_data_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Decrypting empty data raises ValueError."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        with pytest.raises(ValueError, match="cannot be empty"):
            await encryption_service.decrypt_data(
                db_session, b"", voice_entry.id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_is_encrypted_returns_true_for_active_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """is_encrypted returns True when active DEK exists."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Initially not encrypted
        assert not await encryption_service.is_encrypted(
            db_session, voice_entry.id
        )

        # After encryption
        await encryption_service.encrypt_data(
            db_session, "data", voice_entry.id, test_user.id
        )

        assert await encryption_service.is_encrypted(
            db_session, voice_entry.id
        )

    @pytest.mark.asyncio
    async def test_is_encrypted_returns_false_after_destruction(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """is_encrypted returns False after DEK destruction."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        await encryption_service.encrypt_data(
            db_session, "data", voice_entry.id, test_user.id
        )
        assert await encryption_service.is_encrypted(
            db_session, voice_entry.id
        )

        await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert not await encryption_service.is_encrypted(
            db_session, voice_entry.id
        )

    @pytest.mark.asyncio
    async def test_get_dek_info(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """get_dek_info returns metadata without decrypting."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        await encryption_service.encrypt_data(
            db_session, "data", voice_entry.id, test_user.id
        )

        info = await encryption_service.get_dek_info(
            db_session, voice_entry.id
        )

        assert info is not None
        assert info["voice_entry_id"] == voice_entry.id
        assert info["encryption_version"] == "local-v1"
        assert info["key_version"] == 1
        assert info["is_deleted"] is False
        assert "created_at" in info


# =============================================================================
# Multi-User Isolation Tests
# =============================================================================


class TestMultiUserIsolation:
    """Tests for multi-user data isolation."""

    @pytest.fixture
    def encryption_service(self) -> EnvelopeEncryptionService:
        """Create encryption service."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        return EnvelopeEncryptionService(provider)

    @pytest.fixture
    async def second_user(self, db_session: AsyncSession):
        """Create a second test user."""
        from app.schemas.auth import UserCreate
        from app.services.database import db_service

        user_data = UserCreate(
            email="seconduser@example.com",
            password="SecondPassword123!"
        )
        user = await db_service.create_user(db_session, user_data)
        await db_session.commit()
        await db_session.refresh(user)
        return user

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_users_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        second_user,
        tmp_path: Path,
    ):
        """User 2 cannot retrieve User 1's DEK."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # User 1 creates encrypted data
        await encryption_service.encrypt_data(
            db_session, "user 1 secret", voice_entry.id, test_user.id
        )

        # User 1 can retrieve their DEK
        dek_user1 = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert dek_user1 is not None

        # User 2 cannot retrieve User 1's DEK
        dek_user2 = await encryption_service.get_dek(
            db_session, voice_entry.id, second_user.id
        )
        assert dek_user2 is None

    @pytest.mark.asyncio
    async def test_user_cannot_decrypt_other_users_data(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        second_user,
        tmp_path: Path,
    ):
        """User 2 cannot decrypt User 1's encrypted data."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # User 1 encrypts data
        encrypted = await encryption_service.encrypt_data(
            db_session, "user 1 secret", voice_entry.id, test_user.id
        )

        # User 2 trying to decrypt fails (no DEK found)
        with pytest.raises(DEKNotFoundError):
            await encryption_service.decrypt_data(
                db_session, encrypted, voice_entry.id, second_user.id
            )

    @pytest.mark.asyncio
    async def test_different_users_different_voice_entries(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        second_user,
        tmp_path: Path,
    ):
        """Different users encrypt their own VoiceEntries independently."""
        # Each user has their own VoiceEntry (realistic scenario)
        voice_entry_1 = await create_voice_entry(db_session, test_user.id, tmp_path)
        voice_entry_2 = await create_voice_entry(db_session, second_user.id, tmp_path)

        # User 1 encrypts their VoiceEntry
        encrypted_1 = await encryption_service.encrypt_data(
            db_session, "user 1 data", voice_entry_1.id, test_user.id
        )

        # User 2 encrypts their VoiceEntry
        encrypted_2 = await encryption_service.encrypt_data(
            db_session, "user 2 data", voice_entry_2.id, second_user.id
        )

        # Both have separate DEKs
        dek_1 = await encryption_service.get_dek(
            db_session, voice_entry_1.id, test_user.id
        )
        dek_2 = await encryption_service.get_dek(
            db_session, voice_entry_2.id, second_user.id
        )

        assert dek_1.id != dek_2.id

        # Each user can decrypt their own data
        decrypted_1 = await encryption_service.decrypt_data(
            db_session, encrypted_1, voice_entry_1.id, test_user.id
        )
        decrypted_2 = await encryption_service.decrypt_data(
            db_session, encrypted_2, voice_entry_2.id, second_user.id
        )

        assert decrypted_1.decode() == "user 1 data"
        assert decrypted_2.decode() == "user 2 data"


# =============================================================================
# File Encryption Tests
# =============================================================================


class TestFileEncryption:
    """Tests for file encryption/decryption."""

    @pytest.fixture
    def encryption_service(self) -> EnvelopeEncryptionService:
        """Create encryption service."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        return EnvelopeEncryptionService(provider)

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_file_roundtrip(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """File encrypts and decrypts correctly."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Create test file
        original_file = tmp_path / "original.wav"
        original_content = b"RIFF" + os.urandom(1000)  # Fake audio data
        original_file.write_bytes(original_content)

        encrypted_file = tmp_path / "original.wav.enc"
        decrypted_file = tmp_path / "decrypted.wav"

        # Encrypt
        await encryption_service.encrypt_file(
            db_session,
            input_path=original_file,
            output_path=encrypted_file,
            voice_entry_id=voice_entry.id,
            user_id=test_user.id,
        )

        assert encrypted_file.exists()
        assert encrypted_file.read_bytes() != original_content

        # Decrypt
        await encryption_service.decrypt_file(
            db_session,
            input_path=encrypted_file,
            output_path=decrypted_file,
            voice_entry_id=voice_entry.id,
            user_id=test_user.id,
        )

        assert decrypted_file.exists()
        assert decrypted_file.read_bytes() == original_content

    @pytest.mark.asyncio
    async def test_encrypt_nonexistent_file_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Encrypting nonexistent file raises FileNotFoundError."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)
        with pytest.raises(FileNotFoundError):
            await encryption_service.encrypt_file(
                db_session,
                input_path=tmp_path / "nonexistent.wav",
                output_path=tmp_path / "output.enc",
                voice_entry_id=voice_entry.id,
                user_id=test_user.id,
            )

    @pytest.mark.asyncio
    async def test_decrypt_file_after_dek_destroyed_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Cannot decrypt file after DEK is destroyed."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Create and encrypt file
        original_file = tmp_path / "original.wav"
        original_file.write_bytes(b"audio data")
        encrypted_file = tmp_path / "original.wav.enc"

        await encryption_service.encrypt_file(
            db_session,
            original_file,
            encrypted_file,
            voice_entry.id,
            test_user.id,
        )

        # Destroy DEK
        await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )

        # Attempt to decrypt fails
        with pytest.raises(DEKDestroyedError):
            await encryption_service.decrypt_file(
                db_session,
                encrypted_file,
                tmp_path / "decrypted.wav",
                voice_entry.id,
                test_user.id,
            )


# =============================================================================
# One DEK per VoiceEntry Design Tests
# =============================================================================


class TestOneDEKPerVoiceEntry:
    """Tests verifying the one DEK per VoiceEntry design."""

    @pytest.fixture
    def encryption_service(self) -> EnvelopeEncryptionService:
        """Create encryption service."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        return EnvelopeEncryptionService(provider)

    @pytest.mark.asyncio
    async def test_same_dek_encrypts_audio_transcription_cleaned(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Same DEK is used for audio, transcription, and cleaned entry data."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Encrypt "audio" (simulated)
        encrypted_audio = await encryption_service.encrypt_data(
            db_session, "audio bytes", voice_entry.id, test_user.id
        )

        # Get DEK after first encryption
        dek_after_audio = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )

        # Encrypt "transcription"
        encrypted_transcription = await encryption_service.encrypt_data(
            db_session, "transcribed text", voice_entry.id, test_user.id
        )

        # Encrypt "cleaned entry"
        encrypted_cleaned = await encryption_service.encrypt_data(
            db_session, "cleaned text with analysis", voice_entry.id, test_user.id
        )

        # Verify same DEK is used for all
        dek_after_all = await encryption_service.get_dek(
            db_session, voice_entry.id, test_user.id
        )
        assert dek_after_audio.id == dek_after_all.id

        # Verify all can be decrypted
        assert (await encryption_service.decrypt_data(
            db_session, encrypted_audio, voice_entry.id, test_user.id
        )).decode() == "audio bytes"

        assert (await encryption_service.decrypt_data(
            db_session, encrypted_transcription, voice_entry.id, test_user.id
        )).decode() == "transcribed text"

        assert (await encryption_service.decrypt_data(
            db_session, encrypted_cleaned, voice_entry.id, test_user.id
        )).decode() == "cleaned text with analysis"

    @pytest.mark.asyncio
    async def test_destroying_dek_makes_all_entry_data_unrecoverable(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        tmp_path: Path,
    ):
        """Destroying DEK makes audio, transcription, and cleaned entry all unrecoverable."""
        voice_entry = await create_voice_entry(db_session, test_user.id, tmp_path)

        # Encrypt multiple pieces of data for the entry
        encrypted_audio = await encryption_service.encrypt_data(
            db_session, "audio", voice_entry.id, test_user.id
        )
        encrypted_transcription = await encryption_service.encrypt_data(
            db_session, "transcription", voice_entry.id, test_user.id
        )
        encrypted_cleaned = await encryption_service.encrypt_data(
            db_session, "cleaned", voice_entry.id, test_user.id
        )

        # Destroy the DEK (GDPR deletion)
        await encryption_service.destroy_dek(
            db_session, voice_entry.id, test_user.id
        )

        # All encrypted data is now unrecoverable
        with pytest.raises(DEKDestroyedError):
            await encryption_service.decrypt_data(
                db_session, encrypted_audio, voice_entry.id, test_user.id
            )

        with pytest.raises(DEKDestroyedError):
            await encryption_service.decrypt_data(
                db_session, encrypted_transcription, voice_entry.id, test_user.id
            )

        with pytest.raises(DEKDestroyedError):
            await encryption_service.decrypt_data(
                db_session, encrypted_cleaned, voice_entry.id, test_user.id
            )
