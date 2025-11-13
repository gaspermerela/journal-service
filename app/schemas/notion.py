"""
Pydantic schemas for Notion integration endpoints.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


# Configuration Schemas

class NotionConfigureRequest(BaseModel):
    """Request schema for configuring Notion integration."""

    api_key: str = Field(
        ...,
        min_length=1,
        description="Notion API key (will be encrypted before storage)"
    )
    database_id: str = Field(
        ...,
        min_length=1,
        description="Notion database ID to sync dreams to"
    )
    auto_sync: bool = Field(
        default=True,
        description="Enable automatic sync after cleanup completion"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_key": "secret_abc123...",
                "database_id": "a1b2c3d4e5f6...",
                "auto_sync": True
            }
        }
    )


class NotionConfigureResponse(BaseModel):
    """Response schema after configuring Notion integration."""

    message: str = Field(..., description="Success message")
    database_title: str = Field(..., description="Title of the validated Notion database")
    auto_sync: bool = Field(..., description="Auto-sync enabled status")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Notion integration configured successfully",
                "database_title": "Dream Journal",
                "auto_sync": True
            }
        }
    )


class NotionSettingsResponse(BaseModel):
    """Response schema for retrieving Notion settings."""

    enabled: bool = Field(..., description="Whether Notion integration is enabled")
    database_id: Optional[str] = Field(None, description="Configured Notion database ID")
    auto_sync: bool = Field(..., description="Auto-sync enabled status")
    has_api_key: bool = Field(..., description="Whether API key is configured (not the actual key)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "enabled": True,
                "database_id": "a1b2c3d4e5f6...",
                "auto_sync": True,
                "has_api_key": True
            }
        }
    )


class NotionDisconnectResponse(BaseModel):
    """Response schema after disconnecting Notion integration."""

    message: str = Field(..., description="Success message")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Notion integration disconnected successfully"
            }
        }
    )


# Sync Schemas

class NotionSyncResponse(BaseModel):
    """Response schema for sync operations."""

    sync_id: UUID = Field(..., description="ID of the sync record")
    entry_id: UUID = Field(..., description="Voice entry ID being synced")
    status: str = Field(..., description="Current sync status")
    message: str = Field(..., description="Status message")
    notion_page_id: Optional[str] = Field(None, description="Notion page ID if sync completed")
    notion_page_url: Optional[str] = Field(None, description="URL to the Notion page if available")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "sync_id": "123e4567-e89b-12d3-a456-426614174000",
                "entry_id": "123e4567-e89b-12d3-a456-426614174001",
                "status": "completed",
                "message": "Dream synced to Notion successfully",
                "notion_page_id": "abc123...",
                "notion_page_url": "https://notion.so/abc123..."
            }
        }
    )


class NotionSyncDetailResponse(BaseModel):
    """Detailed response schema for sync status."""

    id: UUID = Field(..., description="Sync record ID")
    user_id: UUID = Field(..., description="User ID")
    entry_id: UUID = Field(..., description="Voice entry ID")
    cleaned_entry_id: Optional[UUID] = Field(None, description="Cleaned entry ID if available")
    notion_page_id: Optional[str] = Field(None, description="Notion page ID")
    notion_database_id: str = Field(..., description="Target Notion database ID")
    status: str = Field(..., description="Sync status")
    sync_started_at: Optional[datetime] = Field(None, description="When sync started")
    sync_completed_at: Optional[datetime] = Field(None, description="When sync completed")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    retry_count: int = Field(..., description="Number of retry attempts")
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174002",
                "entry_id": "123e4567-e89b-12d3-a456-426614174001",
                "cleaned_entry_id": "123e4567-e89b-12d3-a456-426614174003",
                "notion_page_id": "abc123...",
                "notion_database_id": "db123...",
                "status": "completed",
                "sync_started_at": "2025-01-15T10:30:00Z",
                "sync_completed_at": "2025-01-15T10:30:05Z",
                "error_message": None,
                "retry_count": 0,
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T10:30:05Z"
            }
        }
    )


class NotionSyncListResponse(BaseModel):
    """Response schema for listing sync records."""

    syncs: list[NotionSyncDetailResponse] = Field(..., description="List of sync records")
    total: int = Field(..., description="Total number of sync records")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "syncs": [],
                "total": 0
            }
        }
    )
