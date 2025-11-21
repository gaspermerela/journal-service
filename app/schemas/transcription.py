"""
Pydantic schemas for transcription request/response validation.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TranscriptionBase(BaseModel):
    """Base schema with common transcription fields."""
    status: str
    model_used: str
    language_code: str
    is_primary: bool = False
    beam_size: Optional[int] = None


class TranscriptionTriggerRequest(BaseModel):
    """Schema for triggering a transcription."""
    language: str = Field(
        default="en",
        description="Language code (e.g., 'en', 'es', 'sl') or 'auto' for detection"
    )
    beam_size: Optional[int] = Field(
        default=None,
        description="Beam size for transcription (1-10, higher = more accurate but slower)"
    )

    @field_validator('beam_size')
    @classmethod
    def validate_beam_size(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 10):
            raise ValueError('beam_size must be between 1 and 10')
        return v


class TranscriptionCreate(BaseModel):
    """Schema for creating a new transcription record in database."""
    entry_id: UUID
    status: str = "pending"
    model_used: str
    language_code: str
    is_primary: bool = False


class TranscriptionResponse(TranscriptionBase):
    """Schema for transcription API responses."""
    id: UUID
    entry_id: UUID
    transcribed_text: Optional[str] = None
    transcription_started_at: Optional[datetime] = None
    transcription_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptionListResponse(BaseModel):
    """Schema for listing transcriptions for an entry."""
    transcriptions: list[TranscriptionResponse]
    total: int


class TranscriptionTriggerResponse(BaseModel):
    """Schema for transcription trigger endpoint response."""
    transcription_id: UUID
    entry_id: UUID
    status: str
    message: str = "Transcription started"


class TranscriptionStatusResponse(BaseModel):
    """Schema for transcription status check."""
    id: UUID
    status: str
    transcribed_text: Optional[str] = None
    model_used: str
    language_code: str
    beam_size: Optional[int] = None
    transcription_started_at: Optional[datetime] = None
    transcription_completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    is_primary: bool

    model_config = ConfigDict(from_attributes=True)


class TranscriptionUpdateStatus(BaseModel):
    """Schema for updating transcription status."""
    status: str
    transcription_started_at: Optional[datetime] = None
    transcription_completed_at: Optional[datetime] = None
    transcribed_text: Optional[str] = None
    error_message: Optional[str] = None


class SetPrimaryTranscriptionRequest(BaseModel):
    """Schema for setting a transcription as primary."""
    transcription_id: UUID
