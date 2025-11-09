"""
Pydantic schemas for voice entry request/response validation.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class VoiceEntryBase(BaseModel):
    """Base schema with common fields."""
    original_filename: str
    saved_filename: str
    file_path: str
    entry_type: str = "dream"


class VoiceEntryCreate(BaseModel):
    """Schema for creating a new voice entry."""
    original_filename: str
    saved_filename: str
    file_path: str
    entry_type: str = "dream"
    uploaded_at: datetime


class VoiceEntryResponse(VoiceEntryBase):
    """Schema for voice entry API responses."""
    id: UUID
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
    file_path: str
    entry_type: str
    uploaded_at: datetime
    transcription_status: str
    transcription_language: str
    message: str = "File uploaded and transcription started"


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: str | None = None
