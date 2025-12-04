"""
Tests for envelope encryption service.

Tests cover:
- LocalKEKProvider: KEK derivation, DEK encryption/decryption
- EnvelopeEncryptionService: DEK management, data/file encryption, GDPR deletion
- Multi-user isolation: different users can't access each other's DEKs
"""

import os
import uuid
from pathlib import Path
from unittest.mock import Mock, AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.encryption_providers.local_kek import (
    LocalKEKProvider,
    LocalKEKProviderError,
)
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    EncryptionError,
    DEKNotFoundError,
    DEKDestroyedError,
    create_envelope_encryption_service,
)
from app.models.data_encryption_key import DataEncryptionKey


# =============================================================================
# LocalKEKProvider Unit Tests
# =============================================================================


class TestLocalKEKProvider:
    """Unit tests for LocalKEKProvider."""

    def test_init_valid_master_key(self):
        """Provider initializes with valid master key."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        assert provider.get_provider_version() == "local-v1"

    def test_init_short_master_key_fails(self):
        """Provider rejects master keys shorter than 16 chars."""
        with pytest.raises(ValueError, match="at least 16 characters"):
            LocalKEKProvider(master_key="short")

    def test_init_empty_master_key_fails(self):
        """Provider rejects empty master key."""
        with pytest.raises(ValueError, match="at least 16 characters"):
            LocalKEKProvider(master_key="")

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_roundtrip(self):
        """DEK encrypts and decrypts correctly."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()
        original_dek = os.urandom(32)

        encrypted = await provider.encrypt_dek(original_dek, user_id)
        decrypted = await provider.decrypt_dek(encrypted, user_id)

        assert decrypted == original_dek

    @pytest.mark.asyncio
    async def test_different_users_get_different_encryptions(self):
        """Same DEK encrypted for different users produces different ciphertext."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()
        dek = os.urandom(32)

        encrypted_1 = await provider.encrypt_dek(dek, user_id_1)
        encrypted_2 = await provider.encrypt_dek(dek, user_id_2)

        # Different KEKs (from different user salts) produce different ciphertext
        assert encrypted_1 != encrypted_2

    @pytest.mark.asyncio
    async def test_user_cannot_decrypt_other_users_dek(self):
        """User 2 cannot decrypt DEK encrypted for user 1."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()
        dek = os.urandom(32)

        encrypted_for_user_1 = await provider.encrypt_dek(dek, user_id_1)

        # User 2 trying to decrypt should fail (authentication tag mismatch)
        with pytest.raises(LocalKEKProviderError, match="decryption failed"):
            await provider.decrypt_dek(encrypted_for_user_1, user_id_2)

    @pytest.mark.asyncio
    async def test_encrypt_empty_dek_fails(self):
        """Encrypting empty DEK raises ValueError."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="cannot be empty"):
            await provider.encrypt_dek(b"", user_id)

    @pytest.mark.asyncio
    async def test_decrypt_empty_data_fails(self):
        """Decrypting empty data raises ValueError."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()

        with pytest.raises(ValueError, match="cannot be empty"):
            await provider.decrypt_dek(b"", user_id)

    @pytest.mark.asyncio
    async def test_decrypt_too_short_data_fails(self):
        """Decrypting data shorter than minimum length fails."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()

        # Minimum is nonce (12) + ciphertext (1) + tag (16) = 29 bytes
        with pytest.raises(ValueError, match="too short"):
            await provider.decrypt_dek(b"x" * 20, user_id)

    @pytest.mark.asyncio
    async def test_decrypt_corrupted_data_fails(self):
        """Decrypting corrupted ciphertext fails authentication."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()
        dek = os.urandom(32)

        encrypted = await provider.encrypt_dek(dek, user_id)

        # Corrupt the ciphertext (skip nonce, corrupt middle)
        corrupted = bytearray(encrypted)
        corrupted[15] ^= 0xFF  # Flip bits in ciphertext
        corrupted = bytes(corrupted)

        with pytest.raises(LocalKEKProviderError, match="decryption failed"):
            await provider.decrypt_dek(corrupted, user_id)

    @pytest.mark.asyncio
    async def test_same_encryption_different_nonces(self):
        """Multiple encryptions of same DEK produce different ciphertext (unique nonces)."""
        provider = LocalKEKProvider(master_key="test-master-key-12345678")
        user_id = uuid.uuid4()
        dek = os.urandom(32)

        encrypted_1 = await provider.encrypt_dek(dek, user_id)
        encrypted_2 = await provider.encrypt_dek(dek, user_id)

        # Same plaintext should produce different ciphertext (random nonce)
        assert encrypted_1 != encrypted_2

        # But both should decrypt to same DEK
        decrypted_1 = await provider.decrypt_dek(encrypted_1, user_id)
        decrypted_2 = await provider.decrypt_dek(encrypted_2, user_id)
        assert decrypted_1 == decrypted_2 == dek


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
    ):
        """Creates DEK and stores in database."""
        target_id = uuid.uuid4()

        dek_id = await encryption_service.create_dek(
            db_session,
            user_id=test_user.id,
            target_type="transcription",
            target_id=target_id,
        )

        assert dek_id is not None

        # Verify DEK is in database
        dek_record = await encryption_service.get_dek(
            db_session, "transcription", target_id, test_user.id
        )
        assert dek_record is not None
        assert dek_record.user_id == test_user.id
        assert dek_record.target_type == "transcription"
        assert dek_record.target_id == target_id
        assert dek_record.encryption_version == "local-v1"
        assert not dek_record.is_deleted

    @pytest.mark.asyncio
    async def test_encrypt_decrypt_data_roundtrip(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Data encrypts and decrypts correctly through full service."""
        target_id = uuid.uuid4()
        original_data = "This is my secret dream journal entry."

        # Encrypt
        encrypted = await encryption_service.encrypt_data(
            db_session,
            data=original_data,
            target_type="transcription",
            target_id=target_id,
            user_id=test_user.id,
        )

        assert encrypted != original_data.encode()
        assert len(encrypted) > len(original_data)

        # Decrypt
        decrypted = await encryption_service.decrypt_data(
            db_session,
            encrypted_data=encrypted,
            target_type="transcription",
            target_id=target_id,
            user_id=test_user.id,
        )

        assert decrypted.decode("utf-8") == original_data

    @pytest.mark.asyncio
    async def test_encrypt_data_creates_dek_automatically(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Encrypting data for new target creates DEK automatically."""
        target_id = uuid.uuid4()

        # No DEK exists yet
        assert await encryption_service.get_dek(
            db_session, "voice_entry", target_id, test_user.id
        ) is None

        # Encrypt - should create DEK
        await encryption_service.encrypt_data(
            db_session,
            data="secret data",
            target_type="voice_entry",
            target_id=target_id,
            user_id=test_user.id,
        )

        # DEK should now exist
        dek = await encryption_service.get_dek(
            db_session, "voice_entry", target_id, test_user.id
        )
        assert dek is not None

    @pytest.mark.asyncio
    async def test_encrypt_reuses_existing_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Multiple encryptions for same target use same DEK."""
        target_id = uuid.uuid4()

        # First encryption creates DEK
        await encryption_service.encrypt_data(
            db_session, "data 1", "cleaned_entry", target_id, test_user.id
        )
        dek_1 = await encryption_service.get_dek(
            db_session, "cleaned_entry", target_id, test_user.id
        )

        # Second encryption reuses DEK
        await encryption_service.encrypt_data(
            db_session, "data 2", "cleaned_entry", target_id, test_user.id
        )
        dek_2 = await encryption_service.get_dek(
            db_session, "cleaned_entry", target_id, test_user.id
        )

        assert dek_1.id == dek_2.id

    @pytest.mark.asyncio
    async def test_destroy_dek_gdpr_deletion(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Destroying DEK makes data permanently unrecoverable."""
        target_id = uuid.uuid4()

        # Encrypt some data
        encrypted = await encryption_service.encrypt_data(
            db_session, "secret data", "transcription", target_id, test_user.id
        )

        # Verify we can decrypt
        decrypted = await encryption_service.decrypt_data(
            db_session, encrypted, "transcription", target_id, test_user.id
        )
        assert decrypted.decode() == "secret data"

        # Destroy DEK (GDPR deletion)
        destroyed = await encryption_service.destroy_dek(
            db_session, "transcription", target_id, test_user.id
        )
        assert destroyed is True

        # DEK record should be marked as deleted
        dek = await encryption_service.get_dek(
            db_session, "transcription", target_id, test_user.id
        )
        assert dek.is_deleted
        assert dek.deleted_at is not None

        # Attempting to decrypt should fail
        with pytest.raises(DEKDestroyedError, match="has been destroyed"):
            await encryption_service.decrypt_data(
                db_session, encrypted, "transcription", target_id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_destroy_dek_returns_false_if_not_found(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Destroying nonexistent DEK returns False."""
        result = await encryption_service.destroy_dek(
            db_session, "transcription", uuid.uuid4(), test_user.id
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_encrypt_after_destroy_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Cannot encrypt new data after DEK is destroyed."""
        target_id = uuid.uuid4()

        # Create and destroy DEK
        await encryption_service.encrypt_data(
            db_session, "data", "transcription", target_id, test_user.id
        )
        await encryption_service.destroy_dek(
            db_session, "transcription", target_id, test_user.id
        )

        # Attempting to encrypt should fail
        with pytest.raises(DEKDestroyedError, match="has been destroyed"):
            await encryption_service.encrypt_data(
                db_session, "new data", "transcription", target_id, test_user.id
            )

    @pytest.mark.asyncio
    async def test_decrypt_nonexistent_dek_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Decrypting data with no DEK fails."""
        fake_encrypted = os.urandom(50)

        with pytest.raises(DEKNotFoundError, match="No DEK found"):
            await encryption_service.decrypt_data(
                db_session, fake_encrypted, "transcription", uuid.uuid4(), test_user.id
            )

    @pytest.mark.asyncio
    async def test_encrypt_empty_data_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Encrypting empty data raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await encryption_service.encrypt_data(
                db_session, "", "transcription", uuid.uuid4(), test_user.id
            )

    @pytest.mark.asyncio
    async def test_decrypt_empty_data_fails(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """Decrypting empty data raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await encryption_service.decrypt_data(
                db_session, b"", "transcription", uuid.uuid4(), test_user.id
            )

    @pytest.mark.asyncio
    async def test_is_encrypted_returns_true_for_active_dek(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """is_encrypted returns True when active DEK exists."""
        target_id = uuid.uuid4()

        # Initially not encrypted
        assert not await encryption_service.is_encrypted(
            db_session, "transcription", target_id
        )

        # After encryption
        await encryption_service.encrypt_data(
            db_session, "data", "transcription", target_id, test_user.id
        )

        assert await encryption_service.is_encrypted(
            db_session, "transcription", target_id
        )

    @pytest.mark.asyncio
    async def test_is_encrypted_returns_false_after_destruction(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """is_encrypted returns False after DEK destruction."""
        target_id = uuid.uuid4()

        await encryption_service.encrypt_data(
            db_session, "data", "transcription", target_id, test_user.id
        )
        assert await encryption_service.is_encrypted(
            db_session, "transcription", target_id
        )

        await encryption_service.destroy_dek(
            db_session, "transcription", target_id, test_user.id
        )
        assert not await encryption_service.is_encrypted(
            db_session, "transcription", target_id
        )

    @pytest.mark.asyncio
    async def test_get_dek_info(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
    ):
        """get_dek_info returns metadata without decrypting."""
        target_id = uuid.uuid4()

        await encryption_service.encrypt_data(
            db_session, "data", "transcription", target_id, test_user.id
        )

        info = await encryption_service.get_dek_info(
            db_session, "transcription", target_id
        )

        assert info is not None
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
    ):
        """User 2 cannot retrieve User 1's DEK."""
        target_id = uuid.uuid4()

        # User 1 creates encrypted data
        await encryption_service.encrypt_data(
            db_session, "user 1 secret", "transcription", target_id, test_user.id
        )

        # User 1 can retrieve their DEK
        dek_user1 = await encryption_service.get_dek(
            db_session, "transcription", target_id, test_user.id
        )
        assert dek_user1 is not None

        # User 2 cannot retrieve User 1's DEK
        dek_user2 = await encryption_service.get_dek(
            db_session, "transcription", target_id, second_user.id
        )
        assert dek_user2 is None

    @pytest.mark.asyncio
    async def test_user_cannot_decrypt_other_users_data(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        second_user,
    ):
        """User 2 cannot decrypt User 1's encrypted data."""
        target_id = uuid.uuid4()

        # User 1 encrypts data
        encrypted = await encryption_service.encrypt_data(
            db_session, "user 1 secret", "transcription", target_id, test_user.id
        )

        # User 2 trying to decrypt fails (no DEK found)
        with pytest.raises(DEKNotFoundError):
            await encryption_service.decrypt_data(
                db_session, encrypted, "transcription", target_id, second_user.id
            )

    @pytest.mark.asyncio
    async def test_same_target_id_different_users(
        self,
        encryption_service: EnvelopeEncryptionService,
        db_session: AsyncSession,
        test_user,
        second_user,
    ):
        """Same target_id can be encrypted separately for different users."""
        target_id = uuid.uuid4()  # Same target ID

        # User 1 encrypts
        encrypted_1 = await encryption_service.encrypt_data(
            db_session, "user 1 data", "transcription", target_id, test_user.id
        )

        # User 2 encrypts same target_id
        encrypted_2 = await encryption_service.encrypt_data(
            db_session, "user 2 data", "transcription", target_id, second_user.id
        )

        # Both have separate DEKs
        dek_1 = await encryption_service.get_dek(
            db_session, "transcription", target_id, test_user.id
        )
        dek_2 = await encryption_service.get_dek(
            db_session, "transcription", target_id, second_user.id
        )

        assert dek_1.id != dek_2.id

        # Each user can decrypt their own data
        decrypted_1 = await encryption_service.decrypt_data(
            db_session, encrypted_1, "transcription", target_id, test_user.id
        )
        decrypted_2 = await encryption_service.decrypt_data(
            db_session, encrypted_2, "transcription", target_id, second_user.id
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
        target_id = uuid.uuid4()

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
            target_type="voice_entry",
            target_id=target_id,
            user_id=test_user.id,
        )

        assert encrypted_file.exists()
        assert encrypted_file.read_bytes() != original_content

        # Decrypt
        await encryption_service.decrypt_file(
            db_session,
            input_path=encrypted_file,
            output_path=decrypted_file,
            target_type="voice_entry",
            target_id=target_id,
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
        with pytest.raises(FileNotFoundError):
            await encryption_service.encrypt_file(
                db_session,
                input_path=tmp_path / "nonexistent.wav",
                output_path=tmp_path / "output.enc",
                target_type="voice_entry",
                target_id=uuid.uuid4(),
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
        target_id = uuid.uuid4()

        # Create and encrypt file
        original_file = tmp_path / "original.wav"
        original_file.write_bytes(b"audio data")
        encrypted_file = tmp_path / "original.wav.enc"

        await encryption_service.encrypt_file(
            db_session,
            original_file,
            encrypted_file,
            "voice_entry",
            target_id,
            test_user.id,
        )

        # Destroy DEK
        await encryption_service.destroy_dek(
            db_session, "voice_entry", target_id, test_user.id
        )

        # Attempt to decrypt fails
        with pytest.raises(DEKDestroyedError):
            await encryption_service.decrypt_file(
                db_session,
                encrypted_file,
                tmp_path / "decrypted.wav",
                "voice_entry",
                target_id,
                test_user.id,
            )


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestFactoryFunction:
    """Tests for create_envelope_encryption_service factory."""

    def test_create_local_provider(self, monkeypatch):
        """Factory creates service with local provider."""
        # Mock settings to have a valid encryption key
        from app import config
        original_key = config.settings.api_encryption_key

        try:
            # Ensure we have a valid key
            if not original_key or len(original_key) < 16:
                monkeypatch.setattr(
                    config.settings, "api_encryption_key", "test-master-key-12345678"
                )

            service = create_envelope_encryption_service(provider="local")
            assert isinstance(service, EnvelopeEncryptionService)
            assert service.kek_provider.get_provider_version() == "local-v1"
        finally:
            pass  # Original value restored by monkeypatch

    def test_create_unsupported_provider_fails(self, monkeypatch):
        """Factory raises ValueError for unsupported provider."""
        from app import config
        monkeypatch.setattr(
            config.settings, "api_encryption_key", "test-master-key-12345678"
        )

        with pytest.raises(ValueError, match="Unsupported encryption provider"):
            create_envelope_encryption_service(provider="unknown-kms")
