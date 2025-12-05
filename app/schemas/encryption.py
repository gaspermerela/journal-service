"""
Pydantic schemas for envelope encryption operations.

All encryption operations are scoped to VoiceEntry - one DEK per VoiceEntry
encrypts the audio file, transcriptions, and cleaned entries.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DEKInfo(BaseModel):
    """Information about a Data Encryption Key (DEK)."""
    id: UUID = Field(description="DEK record ID")
    user_id: UUID = Field(description="User who owns this DEK")
    voice_entry_id: UUID = Field(description="VoiceEntry this DEK protects")
    encryption_version: str = Field(description="Encryption provider version (e.g., 'local-v1')")
    key_version: int = Field(description="Key version for rotation tracking")
    created_at: datetime = Field(description="When the DEK was created")
    rotated_at: Optional[datetime] = Field(None, description="When the DEK was last rotated")
    is_deleted: bool = Field(description="Whether the DEK has been deleted (GDPR erasure)")

    model_config = {"from_attributes": True}


class EncryptionStatus(BaseModel):
    """Encryption status for a VoiceEntry."""
    voice_entry_id: UUID = Field(description="VoiceEntry ID")
    is_encrypted: bool = Field(description="Whether the VoiceEntry is currently encrypted")
    encryption_version: Optional[str] = Field(None, description="Encryption version if encrypted")
    dek_id: Optional[UUID] = Field(None, description="DEK ID if encrypted")


class EncryptDataRequest(BaseModel):
    """Request to encrypt data for a VoiceEntry."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")
    data: str = Field(description="Data to encrypt (text content)")


class EncryptDataResponse(BaseModel):
    """Response after encrypting data."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")
    dek_id: UUID = Field(description="ID of the DEK used for encryption")
    encryption_version: str = Field(description="Encryption provider version used")
    message: str = Field(description="Human-readable message")


class DecryptDataRequest(BaseModel):
    """Request to decrypt data for a VoiceEntry."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")


class DecryptDataResponse(BaseModel):
    """Response after decrypting data."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")
    data: str = Field(description="Decrypted data")


class DEKDestroyRequest(BaseModel):
    """Request to destroy a DEK (GDPR cryptographic erasure)."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")
    confirm: bool = Field(
        default=False,
        description="Must be True to confirm DEK destruction (all data for entry becomes unrecoverable)"
    )


class DEKDestroyResponse(BaseModel):
    """Response after destroying a DEK."""
    voice_entry_id: UUID = Field(description="ID of the VoiceEntry")
    dek_id: UUID = Field(description="ID of the destroyed DEK")
    destroyed_at: datetime = Field(description="When the DEK was destroyed")
    message: str = Field(description="Human-readable message")


class UserEncryptionPreference(BaseModel):
    """User's encryption preference."""
    encryption_enabled: bool = Field(
        default=True,
        description="Whether to encrypt voice entries at rest (enabled by default, opt-out)"
    )


class EncryptionConfigInfo(BaseModel):
    """System encryption configuration info (for health/status endpoints)."""
    provider: str = Field(description="Encryption provider in use")
    dreams_encryption_available: bool = Field(description="Whether dream encryption is enabled system-wide")
    therapy_encryption_available: bool = Field(description="Whether therapy encryption is enabled system-wide")
    encrypt_audio_files: bool = Field(description="Whether audio files are encrypted")
    encrypt_transcriptions: bool = Field(description="Whether transcriptions are encrypted")
    encrypt_cleaned_entries: bool = Field(description="Whether cleaned entries are encrypted")
