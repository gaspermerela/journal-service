"""
Pydantic schemas for voice entry request/response validation.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict


class VoiceEntryBase(BaseModel):
    """Base schema with common fields."""
    original_filename: str
    saved_filename: str
    entry_type: str = "dream"


class VoiceEntryCreate(BaseModel):
    """Schema for creating a new voice entry."""
    original_filename: str
    saved_filename: str
    file_path: str
    entry_type: str = "dream"
    duration_seconds: float = 0.0
    uploaded_at: datetime
    user_id: Optional[UUID] = None


class VoiceEntryResponse(VoiceEntryBase):
    """Schema for voice entry API responses."""
    id: UUID
    duration_seconds: float
    uploaded_at: datetime
    entry_type: str
    primary_transcription: Optional[Any] = Field(
        default=None,
        description="Primary transcription for this entry, if available"
    )

    model_config = ConfigDict(from_attributes=True)


class VoiceEntryUploadResponse(VoiceEntryResponse):
    """Schema for upload endpoint response with success message."""
    message: str = "File uploaded successfully"


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""
    status: str
    database: str
    timestamp: datetime


class VoiceEntryUploadAndTranscribeResponse(BaseModel):
    """Schema for combined upload and transcribe endpoint response."""
    entry_id: UUID
    transcription_id: UUID
    original_filename: str
    saved_filename: str
    duration_seconds: float
    entry_type: str
    uploaded_at: datetime
    transcription_status: str
    transcription_language: str
    message: str = "File uploaded and transcription started"


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: str | None = None


class TranscriptionSummary(BaseModel):
    """Lightweight transcription info for list views (no text content)."""
    id: UUID
    status: str
    language_code: str
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CleanedEntrySummary(BaseModel):
    """Cleaned entry info for list views with text preview."""
    id: UUID
    status: str
    cleaned_text_preview: Optional[str] = Field(
        None,
        description="First 200 characters of cleaned text"
    )
    analysis: Optional[Dict[str, Any]] = Field(
        None,
        description="Structured analysis (themes, emotions, etc.)"
    )
    error_message: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VoiceEntrySummary(BaseModel):
    """
    Lightweight voice entry schema for list views.

    Excludes text content (transcribed_text, cleaned_text) to keep payload small.
    User clicks entry to see full detail via GET /entries/{id}.
    """
    id: UUID
    original_filename: str
    saved_filename: str
    entry_type: str
    duration_seconds: float
    uploaded_at: datetime

    # Primary transcription metadata (no text)
    primary_transcription: Optional[TranscriptionSummary] = None

    # Latest cleaned entry metadata (no text)
    latest_cleaned_entry: Optional[CleanedEntrySummary] = None

    model_config = ConfigDict(from_attributes=True)


class VoiceEntryListResponse(BaseModel):
    """Paginated list response for voice entries."""
    entries: list[VoiceEntrySummary]
    total: int
    limit: int
    offset: int
