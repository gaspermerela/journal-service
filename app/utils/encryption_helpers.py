"""
Helper functions for envelope encryption integration.

These helpers simplify the integration of encryption into routes and services
by providing common patterns for checking encryption status and decrypting data.
"""
import json
from pathlib import Path
from typing import Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.database import DatabaseService
from app.services.envelope_encryption import EnvelopeEncryptionService
from app.utils.logger import get_logger

logger = get_logger("encryption.helpers")

db_service = DatabaseService()


async def should_encrypt(
    db: AsyncSession,
    user_id: UUID,
    encryption_service: Optional[EnvelopeEncryptionService],
) -> bool:
    """
    Check if data should be encrypted for a user.

    Encryption is enabled when:
    1. The encryption service is available
    2. The user has encryption_enabled = True in their preferences (enabled by default)

    Args:
        db: Database session
        user_id: User's UUID
        encryption_service: Encryption service instance (may be None if unavailable)

    Returns:
        True if data should be encrypted, False otherwise
    """
    if encryption_service is None:
        return False

    try:
        user_prefs = await db_service.get_user_preferences(db, user_id)
        return user_prefs.encryption_enabled
    except Exception as e:
        logger.warning(
            "Failed to check user encryption preference, defaulting to False",
            user_id=str(user_id),
            error=str(e),
        )
        return False


async def decrypt_text_if_encrypted(
    encryption_service: Optional[EnvelopeEncryptionService],
    db: AsyncSession,
    encrypted_bytes: Optional[bytes],
    plaintext: Optional[str],
    voice_entry_id: UUID,
    user_id: UUID,
    is_encrypted: bool,
) -> Optional[str]:
    """
    Decrypt text if it's encrypted, otherwise return the plaintext.

    Handles the dual-storage pattern where both encrypted and plaintext fields
    may exist during migration. Prioritizes encrypted data if is_encrypted flag is set.

    Args:
        encryption_service: Encryption service (may be None)
        db: Database session
        encrypted_bytes: Encrypted data (may be None)
        plaintext: Plaintext data (may be None, for backward compatibility)
        voice_entry_id: VoiceEntry UUID (for DEK lookup)
        user_id: User UUID (for authorization)
        is_encrypted: Flag indicating if the data is encrypted

    Returns:
        Decrypted text or original plaintext, None if no data available

    Raises:
        EncryptionError: If decryption fails
    """
    if is_encrypted and encrypted_bytes is not None:
        if encryption_service is None:
            logger.error(
                "Cannot decrypt - encryption service unavailable",
                voice_entry_id=str(voice_entry_id),
            )
            raise RuntimeError("Encryption service unavailable but data is encrypted")

        decrypted = await encryption_service.decrypt_data(
            db, encrypted_bytes, voice_entry_id, user_id
        )
        return decrypted.decode("utf-8")

    # Fall back to plaintext for unencrypted or legacy data
    return plaintext


async def decrypt_json_if_encrypted(
    encryption_service: Optional[EnvelopeEncryptionService],
    db: AsyncSession,
    encrypted_bytes: Optional[bytes],
    plaintext_dict: Optional[dict],
    voice_entry_id: UUID,
    user_id: UUID,
    is_encrypted: bool,
) -> Optional[dict]:
    """
    Decrypt JSON data if it's encrypted, otherwise return the plaintext dict.

    Similar to decrypt_text_if_encrypted but handles JSON serialization/deserialization.

    Args:
        encryption_service: Encryption service (may be None)
        db: Database session
        encrypted_bytes: Encrypted JSON data (may be None)
        plaintext_dict: Plaintext dict (may be None, for backward compatibility)
        voice_entry_id: VoiceEntry UUID (for DEK lookup)
        user_id: User UUID (for authorization)
        is_encrypted: Flag indicating if the data is encrypted

    Returns:
        Decrypted dict or original plaintext dict, None if no data available

    Raises:
        EncryptionError: If decryption fails
        json.JSONDecodeError: If decrypted data is not valid JSON
    """
    if is_encrypted and encrypted_bytes is not None:
        if encryption_service is None:
            logger.error(
                "Cannot decrypt JSON - encryption service unavailable",
                voice_entry_id=str(voice_entry_id),
            )
            raise RuntimeError("Encryption service unavailable but data is encrypted")

        decrypted = await encryption_service.decrypt_data(
            db, encrypted_bytes, voice_entry_id, user_id
        )
        return json.loads(decrypted.decode("utf-8"))

    # Fall back to plaintext for unencrypted or legacy data
    return plaintext_dict


async def encrypt_text(
    encryption_service: EnvelopeEncryptionService,
    db: AsyncSession,
    text: str,
    voice_entry_id: UUID,
    user_id: UUID,
) -> bytes:
    """
    Encrypt text data.

    Args:
        encryption_service: Encryption service
        db: Database session
        text: Text to encrypt
        voice_entry_id: VoiceEntry UUID (for DEK)
        user_id: User UUID

    Returns:
        Encrypted bytes
    """
    return await encryption_service.encrypt_data(db, text, voice_entry_id, user_id)


async def encrypt_json(
    encryption_service: EnvelopeEncryptionService,
    db: AsyncSession,
    data: Any,
    voice_entry_id: UUID,
    user_id: UUID,
) -> bytes:
    """
    Encrypt JSON-serializable data.

    Args:
        encryption_service: Encryption service
        db: Database session
        data: Data to encrypt (must be JSON-serializable)
        voice_entry_id: VoiceEntry UUID (for DEK)
        user_id: User UUID

    Returns:
        Encrypted bytes
    """
    json_str = json.dumps(data)
    return await encryption_service.encrypt_data(db, json_str, voice_entry_id, user_id)


async def encrypt_audio_file(
    encryption_service: EnvelopeEncryptionService,
    db: AsyncSession,
    file_path: str,
    voice_entry_id: UUID,
    user_id: UUID,
) -> Tuple[str, str]:
    """
    Encrypt an audio file and return the encrypted file path.

    Creates an encrypted copy with .enc suffix appended to the original filename.
    Optionally keeps the original file based on ENCRYPTION_KEEP_ORIGINAL_FILES setting.

    Args:
        encryption_service: Encryption service
        db: Database session
        file_path: Path to the original audio file
        voice_entry_id: VoiceEntry UUID (for DEK)
        user_id: User UUID

    Returns:
        Tuple of (encrypted_file_path, encryption_version)

    Raises:
        EncryptionError: If encryption fails
    """
    original_path = Path(file_path)
    encrypted_path = Path(str(file_path) + ".enc")

    # Encrypt the file
    await encryption_service.encrypt_file(
        db,
        input_path=original_path,
        output_path=encrypted_path,
        voice_entry_id=voice_entry_id,
        user_id=user_id,
    )

    logger.info(
        "Audio file encrypted",
        original_path=str(original_path),
        encrypted_path=str(encrypted_path),
        voice_entry_id=str(voice_entry_id),
    )

    # Delete original unless in dev mode
    if not settings.ENCRYPTION_KEEP_ORIGINAL_FILES:
        try:
            # TODO: Is this enough for GDPR compliance?
            original_path.unlink()
            logger.info(
                "Original audio file deleted after encryption",
                file_path=str(original_path),
            )
        except Exception as e:
            logger.warning(
                "Failed to delete original audio file after encryption",
                file_path=str(original_path),
                error=str(e),
            )

    return str(encrypted_path), encryption_service.kek_provider.VERSION


async def decrypt_audio_to_temp(
    encryption_service: EnvelopeEncryptionService,
    db: AsyncSession,
    encrypted_file_path: str,
    voice_entry_id: UUID,
    user_id: UUID,
) -> Path:
    """
    Decrypt an encrypted audio file to a temporary location.

    The caller is responsible for deleting the temp file after use.

    Args:
        encryption_service: Encryption service
        db: Database session
        encrypted_file_path: Path to the encrypted file (ends with .enc)
        voice_entry_id: VoiceEntry UUID (for DEK)
        user_id: User UUID

    Returns:
        Path to the decrypted temporary file

    Raises:
        EncryptionError: If decryption fails
    """
    encrypted_path = Path(encrypted_file_path)

    # Remove .enc suffix and add .dec suffix
    # e.g., file.mp3.enc -> file.mp3.dec
    original_name = encrypted_path.name.removesuffix(".enc")
    decrypted_path = encrypted_path.parent / (original_name + ".dec")

    await encryption_service.decrypt_file(
        db,
        input_path=encrypted_path,
        output_path=decrypted_path,
        voice_entry_id=voice_entry_id,
        user_id=user_id,
    )

    logger.info(
        "Audio file decrypted to temp location",
        encrypted_path=str(encrypted_path),
        decrypted_path=str(decrypted_path),
        voice_entry_id=str(voice_entry_id),
    )

    return decrypted_path


def cleanup_temp_file(temp_path: Optional[Path]) -> None:
    """
    Safely delete a temporary decrypted file.

    Args:
        temp_path: Path to the temp file (may be None)
    """
    if temp_path is None:
        return

    try:
        if temp_path.exists():
            temp_path.unlink()
            logger.info("Temp decrypted file cleaned up", file_path=str(temp_path))
    except Exception as e:
        logger.warning(
            "Failed to cleanup temp decrypted file",
            file_path=str(temp_path),
            error=str(e),
        )
