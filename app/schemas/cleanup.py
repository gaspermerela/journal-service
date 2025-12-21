"""
Pydantic schemas for LLM cleanup operations.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.cleaned_entry import CleanupStatus


class CleanupTriggerRequest(BaseModel):
    """Request to trigger cleanup for a transcription."""
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM (0.0-2.0, higher = more creative)"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-p sampling for LLM (0.0-1.0, nucleus sampling)"
    )
    llm_model: Optional[str] = Field(
        default=None,
        description="LLM model to use for cleanup (e.g., 'llama-3.3-70b-versatile'). If not provided, uses configured default."
    )
    llm_provider: Optional[str] = Field(
        default=None,
        description="LLM provider (e.g., 'ollama', 'groq'). If not provided, uses configured default."
    )


class CleanupResponse(BaseModel):
    """Response after triggering cleanup."""
    id: UUID = Field(description="Cleanup entry ID")
    voice_entry_id: UUID = Field(description="Voice entry ID")
    transcription_id: UUID = Field(description="Transcription ID")
    status: CleanupStatus = Field(description="Cleanup processing status")
    model_name: str = Field(description="LLM model used for cleanup")
    created_at: datetime = Field(description="When cleanup was created")
    message: str = Field(description="Human-readable message")

    class Config:
        from_attributes = True


class CleanedEntryDetail(BaseModel):
    """Complete details of a cleaned entry."""
    id: UUID = Field(description="Cleanup entry ID")
    voice_entry_id: UUID = Field(description="Voice entry ID")
    transcription_id: UUID = Field(description="Transcription ID")
    user_id: UUID = Field(description="User ID")
    cleaned_text: Optional[str] = Field(None, description="LLM-cleaned text")
    llm_raw_response: Optional[str] = Field(None, description="Raw LLM response before parsing")
    status: CleanupStatus = Field(description="Cleanup processing status")
    model_name: str = Field(description="LLM model used")
    temperature: Optional[float] = Field(None, description="Temperature used for LLM")
    top_p: Optional[float] = Field(None, description="Top-p value used for LLM")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    is_primary: bool = Field(description="Whether this is the primary cleanup to display")
    processing_time_seconds: Optional[float] = Field(None, description="Processing duration")
    created_at: datetime = Field(description="When cleanup was created")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")
    prompt_template_id: Optional[int] = Field(None, description="ID of the prompt template used")
    prompt_name: Optional[str] = Field(None, description="Name of the prompt template used")
    prompt_description: Optional[str] = Field(None, description="Description of the prompt template used")
    # User edit fields
    user_edited_text: Optional[str] = Field(None, description="User-edited text (if edited)")
    user_edited_at: Optional[datetime] = Field(None, description="When user last edited")
    has_user_edit: bool = Field(default=False, description="Whether user has edited this cleanup")

    class Config:
        from_attributes = True


class UserEditRequest(BaseModel):
    """Request to save user-edited cleanup text."""
    edited_text: str = Field(
        ...,
        min_length=1,
        max_length=50000,
        description="User-edited text to replace AI-generated cleanup"
    )

    @field_validator('edited_text')
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Edited text cannot be empty or whitespace only")
        return v


class UploadTranscribeCleanupRequest(BaseModel):
    """Request for combined upload, transcribe, and cleanup workflow."""
    language: str = Field(default="auto", description="Language code or 'auto' for detection")
    entry_type: str = Field(default="dream", description="Type of entry (dream, journal, meeting, note, etc.)")
    beam_size: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Beam size for transcription (1-10, higher = more accurate but slower)"
    )
    temperature: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=2.0,
        description="Temperature for LLM cleanup (0.0-2.0, higher = more creative)"
    )
    top_p: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Top-p sampling for LLM cleanup (0.0-1.0)"
    )


class UploadTranscribeCleanupResponse(BaseModel):
    """Response for combined upload, transcribe, and cleanup workflow."""
    # Entry info
    entry_id: UUID = Field(description="Voice entry ID")
    original_filename: str = Field(description="Original uploaded filename")
    saved_filename: str = Field(description="Saved filename on disk")
    duration_seconds: float = Field(description="Audio duration in seconds")
    entry_type: str = Field(description="Type of entry")
    uploaded_at: datetime = Field(description="Upload timestamp")

    # Transcription info
    transcription_id: UUID = Field(description="Transcription ID")
    transcription_status: str = Field(description="Transcription processing status")
    transcription_language: str = Field(description="Language code for transcription")

    # Cleanup info
    cleanup_id: UUID = Field(description="Cleanup entry ID")
    cleanup_status: CleanupStatus = Field(description="Cleanup processing status")
    cleanup_model: str = Field(description="LLM model for cleanup")

    message: str = Field(description="Human-readable message")

    class Config:
        from_attributes = True
