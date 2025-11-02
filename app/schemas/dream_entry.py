"""
Pydantic schemas for dream entry request/response validation.
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class DreamEntryBase(BaseModel):
    """Base schema with common fields."""
    original_filename: str
    saved_filename: str
    file_path: str


class DreamEntryCreate(BaseModel):
    """Schema for creating a new dream entry."""
    original_filename: str
    saved_filename: str
    file_path: str
    uploaded_at: datetime


class DreamEntryResponse(DreamEntryBase):
    """Schema for dream entry API responses."""
    id: UUID
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DreamEntryUploadResponse(DreamEntryResponse):
    """Schema for upload endpoint response with success message."""
    message: str = "File uploaded successfully"


class HealthResponse(BaseModel):
    """Schema for health check endpoint response."""
    status: str
    database: str
    timestamp: datetime


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    detail: str
    error_code: str | None = None
