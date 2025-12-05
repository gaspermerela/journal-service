"""
Envelope Encryption Service for GDPR-compliant data protection.

Implements the envelope encryption pattern where:
- Each VoiceEntry gets a unique DEK (Data Encryption Key)
- DEKs are encrypted with a KEK (Key Encryption Key) via a provider
- The KEK is derived per-user (local master key) or managed by KMS
- One DEK per VoiceEntry encrypts all related data (audio, transcriptions, cleaned entries)

Features:
- Per-VoiceEntry encryption isolation
- GDPR-compliant deletion (destroy DEK = all entry data unrecoverable)
- Version tracking for provider migration (local → KMS)
- Supports both data (bytes/string) and file encryption

Usage:
    service = create_envelope_encryption_service(provider="local")

    # Encrypt data for a voice entry
    encrypted = await service.encrypt_data(
        db, data, voice_entry_id, user_id
    )

    # Decrypt data
    decrypted = await service.decrypt_data(
        db, encrypted, voice_entry_id, user_id
    )

    # GDPR deletion - destroys all data for the voice entry
    await service.destroy_dek(db, voice_entry_id, user_id)
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union
from uuid import UUID

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.data_encryption_key import DataEncryptionKey
from app.services.encryption_providers.base import KEKProvider
from app.utils.logger import get_logger

logger = get_logger("encryption.envelope")

# Constants
DEK_LENGTH = 32  # AES-256
NONCE_LENGTH = 12  # 96 bits for GCM
CHUNK_SIZE = 64 * 1024  # 64KB chunks for file streaming


class EncryptionError(Exception):
    """Base exception for encryption errors."""

    pass


class DEKNotFoundError(EncryptionError):
    """Raised when DEK is not found for a target."""

    pass


class DEKDestroyedError(EncryptionError):
    """Raised when attempting to use a destroyed DEK."""

    pass


class EnvelopeEncryptionService:
    """
    Envelope encryption service for encrypting sensitive data.

    Uses the envelope encryption pattern:
    - Each VoiceEntry gets a unique DEK (Data Encryption Key)
    - DEKs are encrypted with a KEK (Key Encryption Key)
    - KEK is derived from master key (local) or managed by KMS
    - One DEK per VoiceEntry encrypts all related data

    Thread Safety:
        This service is thread-safe. All operations are stateless
        and use async database sessions.

    Example:
        >>> service = EnvelopeEncryptionService(LocalKEKProvider(master_key))
        >>> # Encrypt transcription text (uses VoiceEntry's DEK)
        >>> encrypted = await service.encrypt_data(
        ...     db, text.encode(), voice_entry_id, user_id
        ... )
        >>> # Later, decrypt
        >>> decrypted = await service.decrypt_data(
        ...     db, encrypted, voice_entry_id, user_id
        ... )
    """

    def __init__(self, kek_provider: KEKProvider):
        """
        Initialize with a KEK provider.

        Args:
            kek_provider: Provider for KEK operations (encrypt/decrypt DEKs)
        """
        self.kek_provider = kek_provider
        logger.info(
            "EnvelopeEncryptionService initialized",
            provider=kek_provider.get_provider_version(),
        )

    # =========================================================================
    # DEK Management
    # =========================================================================

    async def create_dek(
        self,
        db: AsyncSession,
        user_id: UUID,
        voice_entry_id: UUID,
    ) -> UUID:
        """
        Create a new DEK for a VoiceEntry.

        Generates a random 256-bit DEK, encrypts it with the user's KEK,
        and stores the encrypted DEK in the database.

        Args:
            db: Database session
            user_id: Owner user ID
            voice_entry_id: UUID of the VoiceEntry to protect

        Returns:
            UUID of the created DEK record

        Raises:
            EncryptionError: If DEK creation fails
        """
        try:
            # Generate random DEK
            plaintext_dek = os.urandom(DEK_LENGTH)

            # Encrypt DEK with user's KEK
            encrypted_dek = await self.kek_provider.encrypt_dek(plaintext_dek, user_id)

            # Store encrypted DEK in database
            dek_record = DataEncryptionKey(
                user_id=user_id,
                encrypted_dek=encrypted_dek,
                encryption_version=self.kek_provider.get_provider_version(),
                voice_entry_id=voice_entry_id,
            )

            db.add(dek_record)
            await db.flush()

            logger.debug(
                "Created DEK",
                dek_id=str(dek_record.id),
                voice_entry_id=str(voice_entry_id),
                user_id=str(user_id),
            )

            return dek_record.id

        except Exception as e:
            logger.error(
                "Failed to create DEK",
                voice_entry_id=str(voice_entry_id),
                user_id=str(user_id),
                error=str(e),
            )
            raise EncryptionError(f"Failed to create DEK: {e}") from e

    async def get_dek(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> Optional[DataEncryptionKey]:
        """
        Get DEK record for a VoiceEntry.

        Args:
            db: Database session
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID for authorization check

        Returns:
            DataEncryptionKey record or None if not found
        """
        result = await db.execute(
            select(DataEncryptionKey).where(
                DataEncryptionKey.voice_entry_id == voice_entry_id,
                DataEncryptionKey.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def _get_or_create_dek(
        self,
        db: AsyncSession,
        user_id: UUID,
        voice_entry_id: UUID,
    ) -> tuple[bytes, DataEncryptionKey]:
        """
        Get existing DEK or create new one for a VoiceEntry.

        Returns both the plaintext DEK (for immediate use) and the record.

        Args:
            db: Database session
            user_id: User ID
            voice_entry_id: VoiceEntry UUID

        Returns:
            Tuple of (plaintext_dek, dek_record)

        Raises:
            DEKDestroyedError: If DEK exists but was destroyed
            EncryptionError: If DEK operations fail
        """
        dek_record = await self.get_dek(db, voice_entry_id, user_id)

        if dek_record is not None:
            # Check if DEK was destroyed (GDPR deletion)
            if dek_record.is_deleted:
                raise DEKDestroyedError(
                    f"DEK for voice_entry:{voice_entry_id} has been destroyed "
                    "(GDPR deletion performed)"
                )

            # Decrypt existing DEK
            plaintext_dek = await self.kek_provider.decrypt_dek(
                dek_record.encrypted_dek, user_id
            )
            return plaintext_dek, dek_record

        # Create new DEK
        plaintext_dek = os.urandom(DEK_LENGTH)
        encrypted_dek = await self.kek_provider.encrypt_dek(plaintext_dek, user_id)

        dek_record = DataEncryptionKey(
            user_id=user_id,
            encrypted_dek=encrypted_dek,
            encryption_version=self.kek_provider.get_provider_version(),
            voice_entry_id=voice_entry_id,
        )

        db.add(dek_record)
        await db.flush()

        logger.debug(
            "Created DEK on-demand",
            voice_entry_id=str(voice_entry_id),
        )

        return plaintext_dek, dek_record

    async def destroy_dek(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> bool:
        """
        Destroy a DEK (GDPR cryptographic erasure).

        This performs cryptographic erasure by:
        1. Setting deleted_at timestamp
        2. Overwriting encrypted_dek with random bytes
        3. The DEK is gone - all data for the VoiceEntry is unrecoverable

        Args:
            db: Database session
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID for authorization

        Returns:
            True if DEK was destroyed, False if not found

        Note:
            This operation is irreversible. All encrypted data for the
            VoiceEntry (audio, transcriptions, cleaned entries) becomes
            permanently unrecoverable.
        """
        dek_record = await self.get_dek(db, voice_entry_id, user_id)

        if dek_record is None:
            logger.warning(
                "DEK not found for destruction",
                voice_entry_id=str(voice_entry_id),
            )
            return False

        if dek_record.is_deleted:
            logger.debug(
                "DEK already destroyed",
                voice_entry_id=str(voice_entry_id),
            )
            return True

        # Cryptographic erasure: overwrite DEK with random bytes
        dek_record.encrypted_dek = os.urandom(len(dek_record.encrypted_dek))
        dek_record.deleted_at = datetime.now(timezone.utc)

        await db.flush()

        logger.info(
            "Destroyed DEK (GDPR erasure)",
            voice_entry_id=str(voice_entry_id),
            user_id=str(user_id),
        )

        return True

    # =========================================================================
    # Data Encryption/Decryption
    # =========================================================================

    async def encrypt_data(
        self,
        db: AsyncSession,
        data: Union[str, bytes],
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> bytes:
        """
        Encrypt data using the DEK for the VoiceEntry.

        If no DEK exists for the VoiceEntry, one is created automatically.

        Args:
            db: Database session
            data: Data to encrypt (string or bytes)
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID

        Returns:
            Encrypted data bytes (nonce || ciphertext || tag)

        Raises:
            DEKDestroyedError: If DEK was destroyed (GDPR deletion)
            EncryptionError: If encryption fails
        """
        if isinstance(data, str):
            data = data.encode("utf-8")

        if not data:
            raise ValueError("Data cannot be empty")

        try:
            # Get or create DEK for this VoiceEntry
            plaintext_dek, _ = await self._get_or_create_dek(
                db, user_id, voice_entry_id
            )

            # Encrypt data with DEK using AES-GCM
            aesgcm = AESGCM(plaintext_dek)
            nonce = os.urandom(NONCE_LENGTH)
            ciphertext = aesgcm.encrypt(nonce, data, None)

            # Return nonce || ciphertext
            return nonce + ciphertext

        except DEKDestroyedError:
            raise
        except Exception as e:
            logger.error(
                "Failed to encrypt data",
                voice_entry_id=str(voice_entry_id),
                error=str(e),
            )
            raise EncryptionError(f"Failed to encrypt data: {e}") from e

    async def decrypt_data(
        self,
        db: AsyncSession,
        encrypted_data: bytes,
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> bytes:
        """
        Decrypt data using the DEK for the VoiceEntry.

        Args:
            db: Database session
            encrypted_data: Encrypted bytes (as returned by encrypt_data)
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID

        Returns:
            Decrypted data bytes

        Raises:
            DEKNotFoundError: If no DEK exists for VoiceEntry
            DEKDestroyedError: If DEK has been destroyed (GDPR deletion)
            EncryptionError: If decryption fails
        """
        if not encrypted_data:
            raise ValueError("Encrypted data cannot be empty")

        # Minimum: nonce (12) + ciphertext (1) + tag (16)
        min_length = NONCE_LENGTH + 1 + 16
        if len(encrypted_data) < min_length:
            raise ValueError(
                f"Encrypted data too short: {len(encrypted_data)} bytes, "
                f"minimum {min_length}"
            )

        try:
            # Get DEK record
            dek_record = await self.get_dek(db, voice_entry_id, user_id)

            if dek_record is None:
                raise DEKNotFoundError(
                    f"No DEK found for voice_entry:{voice_entry_id}"
                )

            if dek_record.is_deleted:
                raise DEKDestroyedError(
                    f"DEK for voice_entry:{voice_entry_id} has been destroyed"
                )

            # Decrypt DEK using KEK provider
            plaintext_dek = await self.kek_provider.decrypt_dek(
                dek_record.encrypted_dek, user_id
            )

            # Extract nonce and ciphertext
            nonce = encrypted_data[:NONCE_LENGTH]
            ciphertext = encrypted_data[NONCE_LENGTH:]

            # Decrypt data with DEK
            aesgcm = AESGCM(plaintext_dek)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext

        except (DEKNotFoundError, DEKDestroyedError):
            raise
        except Exception as e:
            logger.error(
                "Failed to decrypt data",
                voice_entry_id=str(voice_entry_id),
                error=str(e),
            )
            raise EncryptionError(f"Failed to decrypt data: {e}") from e

    # =========================================================================
    # File Encryption/Decryption
    # =========================================================================

    async def encrypt_file(
        self,
        db: AsyncSession,
        input_path: Path,
        output_path: Path,
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Encrypt a file using the DEK for the VoiceEntry.

        Uses AES-GCM encryption.
        The entire file is encrypted as a single authenticated unit.

        Output format: nonce (12 bytes) || ciphertext || tag (16 bytes)

        Args:
            db: Database session
            input_path: Path to plaintext file
            output_path: Path for encrypted output
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID

        Raises:
            FileNotFoundError: If input file doesn't exist
            EncryptionError: If encryption fails
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")

        try:
            # Get or create DEK
            plaintext_dek, _ = await self._get_or_create_dek(
                db, user_id, voice_entry_id
            )

            # Read entire file (AES-GCM needs all data for authentication)
            with open(input_path, "rb") as f:
                plaintext = f.read()

            # Encrypt with AES-GCM
            aesgcm = AESGCM(plaintext_dek)
            nonce = os.urandom(NONCE_LENGTH)
            ciphertext = aesgcm.encrypt(nonce, plaintext, None)

            # Write encrypted file atomically (temp file + rename)
            temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
            try:
                with open(temp_path, "wb") as f:
                    f.write(nonce)
                    f.write(ciphertext)

                # Atomic rename
                temp_path.rename(output_path)

            except Exception:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise

            logger.debug(
                "Encrypted file",
                input_path=str(input_path),
                output_path=str(output_path),
                voice_entry_id=str(voice_entry_id),
            )

        except Exception as e:
            logger.error(
                "Failed to encrypt file",
                input_path=str(input_path),
                voice_entry_id=str(voice_entry_id),
                error=str(e),
            )
            raise EncryptionError(f"Failed to encrypt file: {e}") from e

    async def decrypt_file(
        self,
        db: AsyncSession,
        input_path: Path,
        output_path: Path,
        voice_entry_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Decrypt a file using the DEK for the VoiceEntry.

        Args:
            db: Database session
            input_path: Path to encrypted file
            output_path: Path for decrypted output
            voice_entry_id: UUID of the VoiceEntry
            user_id: User ID

        Raises:
            FileNotFoundError: If input file doesn't exist
            DEKNotFoundError: If no DEK exists for VoiceEntry
            DEKDestroyedError: If DEK has been destroyed
            EncryptionError: If decryption fails
        """
        if not input_path.exists():
            raise FileNotFoundError(f"Encrypted file not found: {input_path}")

        try:
            # Get DEK record
            dek_record = await self.get_dek(db, voice_entry_id, user_id)

            if dek_record is None:
                raise DEKNotFoundError(f"No DEK found for voice_entry:{voice_entry_id}")

            if dek_record.is_deleted:
                raise DEKDestroyedError(
                    f"DEK for voice_entry:{voice_entry_id} has been destroyed"
                )

            # Decrypt DEK
            plaintext_dek = await self.kek_provider.decrypt_dek(
                dek_record.encrypted_dek, user_id
            )

            # Read encrypted file
            with open(input_path, "rb") as f:
                encrypted_data = f.read()

            # Extract nonce and ciphertext
            nonce = encrypted_data[:NONCE_LENGTH]
            ciphertext = encrypted_data[NONCE_LENGTH:]

            # Decrypt with AES-GCM
            aesgcm = AESGCM(plaintext_dek)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            # Write decrypted file atomically
            temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
            try:
                with open(temp_path, "wb") as f:
                    f.write(plaintext)

                temp_path.rename(output_path)

            except Exception:
                if temp_path.exists():
                    temp_path.unlink()
                raise

            logger.debug(
                "Decrypted file",
                input_path=str(input_path),
                output_path=str(output_path),
                voice_entry_id=str(voice_entry_id),
            )

        except (DEKNotFoundError, DEKDestroyedError):
            raise
        except Exception as e:
            logger.error(
                "Failed to decrypt file",
                input_path=str(input_path),
                voice_entry_id=str(voice_entry_id),
                error=str(e),
            )
            raise EncryptionError(f"Failed to decrypt file: {e}") from e

    # =========================================================================
    # Utility Methods
    # =========================================================================

    async def get_dek_info(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
    ) -> Optional[dict]:
        """
        Get DEK metadata without decrypting.

        Args:
            db: Database session
            voice_entry_id: UUID of the VoiceEntry

        Returns:
            Dict with encryption_version, key_version, created_at, etc.
            None if no DEK exists
        """
        result = await db.execute(
            select(DataEncryptionKey).where(
                DataEncryptionKey.voice_entry_id == voice_entry_id,
            )
        )
        dek = result.scalar_one_or_none()

        if dek is None:
            return None

        return {
            "id": dek.id,
            "voice_entry_id": dek.voice_entry_id,
            "encryption_version": dek.encryption_version,
            "key_version": dek.key_version,
            "created_at": dek.created_at,
            "rotated_at": dek.rotated_at,
            "is_deleted": dek.is_deleted,
            "deleted_at": dek.deleted_at,
        }

    async def is_encrypted(
        self,
        db: AsyncSession,
        voice_entry_id: UUID,
    ) -> bool:
        """
        Check if a VoiceEntry has an active DEK.

        Args:
            db: Database session
            voice_entry_id: UUID of the VoiceEntry

        Returns:
            True if active DEK exists (not destroyed)
        """
        result = await db.execute(
            select(DataEncryptionKey.id).where(
                DataEncryptionKey.voice_entry_id == voice_entry_id,
                DataEncryptionKey.deleted_at.is_(None),
            )
        )
        return result.scalar_one_or_none() is not None


# =============================================================================
# Factory Function
# =============================================================================


def create_envelope_encryption_service(
    provider: str = "local",
) -> EnvelopeEncryptionService:
    """
    Factory function to create envelope encryption service.

    Args:
        provider: Provider type ("local" or future "aws-kms", "gcp-kms")

    Returns:
        Configured EnvelopeEncryptionService

    Raises:
        ValueError: If provider is not supported

    Example:
        >>> service = create_envelope_encryption_service(provider="local")
    """
    from app.config import settings

    if provider == "local":
        from app.services.encryption_providers.local_kek import LocalKEKProvider

        kek_provider = LocalKEKProvider(master_key=settings.api_encryption_key)
        return EnvelopeEncryptionService(kek_provider)

    # Future providers
    # elif provider == "aws-kms":
    #     from app.services.encryption_providers.aws_kms import AWSKMSProvider
    #     kek_provider = AWSKMSProvider(key_id=settings.AWS_KMS_KEY_ID)
    #     return EnvelopeEncryptionService(kek_provider)

    else:
        raise ValueError(f"Unsupported encryption provider: {provider}")


# =============================================================================
# Dependency Injection Helper
# =============================================================================


def get_encryption_service(request: Request) -> Optional[EnvelopeEncryptionService]:
    """
    Dependency to get encryption service from app state.

    Unlike other services, encryption is optional - returns None if not available.
    Routes should check if service is None before using encryption features.

    Args:
        request: FastAPI request object

    Returns:
        EnvelopeEncryptionService instance or None if not available

    Example:
        >>> @router.post("/upload")
        >>> async def upload(
        >>>     encryption_service: Optional[EnvelopeEncryptionService] = Depends(get_encryption_service)
        >>> ):
        >>>     if encryption_service and should_encrypt:
        >>>         encrypted = await encryption_service.encrypt_data(...)
    """
    return getattr(request.app.state, "encryption_service", None)
