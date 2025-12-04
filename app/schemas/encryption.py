"""
Pydantic schemas for envelope encryption operations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DEKInfo(BaseModel):
    """Information about a Data Encryption Key (DEK)."""
    id: UUID = Field(description="DEK record ID")
    user_id: UUID = Field(description="User who owns this DEK")
    target_type: str = Field(description="Type of encrypted target (voice_entry, transcription, cleaned_entry)")
    target_id: UUID = Field(description="ID of the encrypted target")
    encryption_version: str = Field(description="Encryption provider version (e.g., 'local-v1')")
    key_version: int = Field(description="Key version for rotation tracking")
    created_at: datetime = Field(description="When the DEK was created")
    rotated_at: Optional[datetime] = Field(None, description="When the DEK was last rotated")
    is_deleted: bool = Field(description="Whether the DEK has been deleted (GDPR erasure)")

    model_config = {"from_attributes": True}


class EncryptionStatus(BaseModel):
    """Encryption status for a resource."""
    target_type: str = Field(description="Type of resource")
    target_id: UUID = Field(description="Resource ID")
    is_encrypted: bool = Field(description="Whether the resource is currently encrypted")
    encryption_version: Optional[str] = Field(None, description="Encryption version if encrypted")
    dek_id: Optional[UUID] = Field(None, description="DEK ID if encrypted")


class EncryptDataRequest(BaseModel):
    """Request to encrypt data for a target."""
    target_type: str = Field(description="Type of target (voice_entry, transcription, cleaned_entry)")
    target_id: UUID = Field(description="ID of the target")
    data: str = Field(description="Data to encrypt (text content)")


class EncryptDataResponse(BaseModel):
    """Response after encrypting data."""
    target_type: str = Field(description="Type of encrypted target")
    target_id: UUID = Field(description="ID of the encrypted target")
    dek_id: UUID = Field(description="ID of the DEK used for encryption")
    encryption_version: str = Field(description="Encryption provider version used")
    message: str = Field(description="Human-readable message")


class DecryptDataRequest(BaseModel):
    """Request to decrypt data for a target."""
    target_type: str = Field(description="Type of target")
    target_id: UUID = Field(description="ID of the target")


class DecryptDataResponse(BaseModel):
    """Response after decrypting data."""
    target_type: str = Field(description="Type of decrypted target")
    target_id: UUID = Field(description="ID of the decrypted target")
    data: str = Field(description="Decrypted data")


class DEKDestroyRequest(BaseModel):
    """Request to destroy a DEK (GDPR cryptographic erasure)."""
    target_type: str = Field(description="Type of target")
    target_id: UUID = Field(description="ID of the target")
    confirm: bool = Field(
        default=False,
        description="Must be True to confirm DEK destruction (data becomes unrecoverable)"
    )


class DEKDestroyResponse(BaseModel):
    """Response after destroying a DEK."""
    target_type: str = Field(description="Type of target")
    target_id: UUID = Field(description="ID of the target")
    dek_id: UUID = Field(description="ID of the destroyed DEK")
    destroyed_at: datetime = Field(description="When the DEK was destroyed")
    message: str = Field(description="Human-readable message")


class UserEncryptionPreference(BaseModel):
    """User's encryption preference."""
    encryption_enabled: bool = Field(
        default=False,
        description="Whether to encrypt dream entries at rest (opt-in)"
    )


class EncryptionConfigInfo(BaseModel):
    """System encryption configuration info (for health/status endpoints)."""
    provider: str = Field(description="Encryption provider in use")
    dreams_encryption_available: bool = Field(description="Whether dream encryption is enabled system-wide")
    therapy_encryption_available: bool = Field(description="Whether therapy encryption is enabled system-wide")
    encrypt_audio_files: bool = Field(description="Whether audio files are encrypted")
    encrypt_transcriptions: bool = Field(description="Whether transcriptions are encrypted")
    encrypt_cleaned_entries: bool = Field(description="Whether cleaned entries are encrypted")
