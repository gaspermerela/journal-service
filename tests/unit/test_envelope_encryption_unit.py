"""
Unit tests for envelope encryption service.

Tests cover:
- LocalKEKProvider: KEK derivation, DEK encryption/decryption
- Factory function for service creation
"""

import os
import uuid

import pytest

from app.services.encryption_providers.local_kek import (
    LocalKEKProvider,
    LocalKEKProviderError,
)
from app.services.envelope_encryption import (
    EnvelopeEncryptionService,
    create_envelope_encryption_service,
)


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
# Factory Function Tests
# =============================================================================


class TestFactoryFunction:
    """Tests for create_envelope_encryption_service factory."""

    def test_create_local_provider(self):
        """Factory creates service with local provider."""
        # The factory uses settings.api_encryption_key which should be set
        # via API_ENCRYPTION_KEY env var (already set in test .env or conftest)
        service = create_envelope_encryption_service(provider="local")
        assert isinstance(service, EnvelopeEncryptionService)
        assert service.kek_provider.get_provider_version() == "local-v1"

    def test_create_unsupported_provider_fails(self):
        """Factory raises ValueError for unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported encryption provider"):
            create_envelope_encryption_service(provider="unknown-kms")
