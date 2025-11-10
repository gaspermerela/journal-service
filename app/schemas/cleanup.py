"""
Pydantic schemas for LLM cleanup operations.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.cleaned_entry import CleanupStatus

# TODO: Here we have lots of dream specific terminology. We should refactor it in the future to logically separate dream-specific logic
class CleanupAnalysis(BaseModel):
    """Structured analysis extracted from LLM cleanup."""
    themes: List[str] = Field(default_factory=list, description="Key themes identified")
    emotions: List[str] = Field(default_factory=list, description="Emotions detected")
    characters: List[str] = Field(default_factory=list, description="People or entities mentioned")
    locations: List[str] = Field(default_factory=list, description="Places mentioned")


class CleanupTriggerRequest(BaseModel):
    """Request to trigger cleanup for a transcription."""
    # Empty for now, could add options like custom_prompt in future
    pass


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
    analysis: Optional[Dict[str, Any]] = Field(None, description="Structured analysis")
    status: CleanupStatus = Field(description="Cleanup processing status")
    model_name: str = Field(description="LLM model used")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    processing_time_seconds: Optional[float] = Field(None, description="Processing duration")
    created_at: datetime = Field(description="When cleanup was created")
    processing_started_at: Optional[datetime] = Field(None, description="Processing start time")
    processing_completed_at: Optional[datetime] = Field(None, description="Processing completion time")

    class Config:
        from_attributes = True


class UploadTranscribeCleanupRequest(BaseModel):
    """Request for combined upload, transcribe, and cleanup workflow."""
    language: str = Field(default="auto", description="Language code or 'auto' for detection")
    entry_type: str = Field(default="dream", description="Type of entry (dream, journal, meeting, note, etc.)")


class UploadTranscribeCleanupResponse(BaseModel):
    """Response for combined upload, transcribe, and cleanup workflow."""
    # Entry info
    entry_id: UUID = Field(description="Voice entry ID")
    original_filename: str = Field(description="Original uploaded filename")
    saved_filename: str = Field(description="Saved filename on disk")
    file_path: str = Field(description="Full path to saved file")
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
