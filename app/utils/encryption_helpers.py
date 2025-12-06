"""
Helper functions for envelope encryption integration.

These helpers simplify the integration of encryption into routes and services
by providing common patterns for encrypting and decrypting data.

Note: Encryption is always on - there is no user preference toggle.
The app fails at startup if the encryption service is unavailable.
"""
import json
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.envelope_encryption import EnvelopeEncryptionService
from app.utils.logger import get_logger

logger = get_logger("encryption.helpers")


class EncryptionServiceUnavailableError(Exception):
    """Raised when encryption is required but the service is unavailable."""
    pass


async def decrypt_text(
    encryption_service: Optional[EnvelopeEncryptionService],
    db: AsyncSession,
    encrypted_bytes: Optional[bytes],
    voice_entry_id: UUID,
    user_id: UUID,
) -> Optional[str]:
    """
    Decrypt text data.

    Args:
        encryption_service: Encryption service
        db: Database session
        encrypted_bytes: Encrypted data (may be None if no data)
        voice_entry_id: VoiceEntry UUID (for DEK lookup)
        user_id: User UUID (for authorization)

    Returns:
        Decrypted text, or None if encrypted_bytes is None or decryption fails

    Raises:
        RuntimeError: If encryption_service is None but encrypted_bytes is provided
    """
    if encrypted_bytes is None:
        return None

    if encryption_service is None:
        raise RuntimeError("Encryption service unavailable")

    try:
        decrypted = await encryption_service.decrypt_data(
            db, encrypted_bytes, voice_entry_id, user_id
        )
        return decrypted.decode("utf-8")
    except Exception as e:
        logger.error(
            "Failed to decrypt text",
            voice_entry_id=str(voice_entry_id),
            error=str(e),
        )
        return None


async def decrypt_json(
    encryption_service: Optional[EnvelopeEncryptionService],
    db: AsyncSession,
    encrypted_bytes: Optional[bytes],
    voice_entry_id: UUID,
    user_id: UUID,
) -> Optional[dict]:
    """
    Decrypt JSON data.

    Args:
        encryption_service: Encryption service
        db: Database session
        encrypted_bytes: Encrypted JSON data (may be None if no data)
        voice_entry_id: VoiceEntry UUID (for DEK lookup)
        user_id: User UUID (for authorization)

    Returns:
        Decrypted dict, or None if encrypted_bytes is None or decryption fails

    Raises:
        RuntimeError: If encryption_service is None but encrypted_bytes is provided
    """
    if encrypted_bytes is None:
        return None

    if encryption_service is None:
        raise RuntimeError("Encryption service unavailable")

    try:
        decrypted = await encryption_service.decrypt_data(
            db, encrypted_bytes, voice_entry_id, user_id
        )
        return json.loads(decrypted.decode("utf-8"))
    except Exception as e:
        logger.error(
            "Failed to decrypt JSON",
            voice_entry_id=str(voice_entry_id),
            error=str(e),
        )
        return None


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
    The original file is deleted after successful encryption.

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

    # Delete original file after successful encryption
    try:
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

    # Remove .enc suffix to get original filename with audio extension
    # e.g., file.mp3.enc -> file.mp3
    # We add a unique suffix to avoid collision with original file
    # e.g., file.mp3.enc -> file_decrypted_abc123.mp3
    original_name = encrypted_path.name.removesuffix(".enc")
    stem = Path(original_name).stem
    suffix = Path(original_name).suffix  # .mp3, .wav, etc.
    unique_id = uuid.uuid4().hex[:8]
    decrypted_path = encrypted_path.parent / f"{stem}_decrypted_{unique_id}{suffix}"

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
