"""
Pydantic schemas for transcription request/response validation.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator


class TranscriptionSegment(BaseModel):
    """Individual transcription segment with optional speaker info."""
    id: int = Field(description="Segment index")
    start: float = Field(description="Start time in seconds")
    end: float = Field(description="End time in seconds")
    text: str = Field(description="Segment text")
    speaker: Optional[str] = Field(
        default=None,
        description="Speaker label (e.g., 'Speaker 1', 'Speaker 2')"
    )


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
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Temperature for transcription sampling (0.0-1.0, higher = more random)"
    )
    transcription_model: Optional[str] = Field(
        default=None,
        description="Transcription model to use (e.g., 'whisper-large-v3'). If not provided, uses configured default."
    )
    transcription_provider: Optional[str] = Field(
        default=None,
        description="Transcription provider (e.g., 'groq', 'assemblyai', 'clarin-slovene-asr-pyannote'). If not provided, uses configured default."
    )
    enable_diarization: bool = Field(
        default=False,
        description="Enable speaker diarization to identify different speakers"
    )
    speaker_count: int = Field(
        default=1,
        ge=1,
        le=10,
        description="Expected number of speakers (1-10). Set > 1 to enable diarization."
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
    beam_size: Optional[int] = None
    temperature: Optional[float] = None
    enable_diarization: bool = False
    speaker_count: int = 1


class TranscriptionResponse(TranscriptionBase):
    """Schema for transcription API responses."""
    id: UUID
    entry_id: UUID
    transcribed_text: Optional[str] = None
    temperature: Optional[float] = None
    enable_diarization: bool = False
    speaker_count: int = 1
    segments: Optional[list[TranscriptionSegment]] = None
    diarization_applied: bool = False
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
    temperature: Optional[float] = None
    enable_diarization: bool = False
    speaker_count: int = 1
    segments: Optional[list[TranscriptionSegment]] = None
    diarization_applied: bool = False
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
