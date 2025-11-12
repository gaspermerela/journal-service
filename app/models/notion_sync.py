"""
NotionSync model for tracking Notion synchronization status.
"""
import uuid
import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, DateTime, Integer, Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.voice_entry import VoiceEntry
    from app.models.cleaned_entry import CleanedEntry


class SyncStatus(str, enum.Enum):
    """Notion sync status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class NotionSync(Base):
    """
    Track Notion synchronization status for entries.

    Attributes:
        id: Unique identifier (UUID4)
        user_id: Foreign key to users table
        entry_id: Foreign key to voice_entries table (voice_entry.id)
        cleaned_entry_id: Foreign key to cleaned_entries table (optional)
        notion_page_id: Notion page ID after successful creation
        notion_database_id: Target Notion database ID
        status: Sync status (pending, processing, completed, failed, retrying)
        sync_started_at: When sync processing began
        sync_completed_at: When sync finished
        error_message: Error details if status is 'failed'
        retry_count: Number of retry attempts
        last_synced_hash: SHA256 hash of content for change detection
        created_at: Record creation time
        updated_at: Last update time
    """

    __tablename__ = "notion_syncs"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.voice_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    cleaned_entry_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.cleaned_entries.id", ondelete="SET NULL"),
        nullable=True
    )

    # Notion identifiers
    notion_page_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True
    )

    notion_database_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    # Status tracking
    status: Mapped[SyncStatus] = mapped_column(
        SQLEnum(
            SyncStatus,
            name="syncstatus",
            schema="journal",
            create_constraint=False,
            native_enum=False,
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=SyncStatus.PENDING,
        index=True
    )

    sync_started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    sync_completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True
    )

    # Retry logic
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0"
    )

    # Change detection (SHA256 hash)
    last_synced_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notion_syncs"
    )

    entry: Mapped["VoiceEntry"] = relationship(
        "VoiceEntry"
    )

    cleaned_entry: Mapped[Optional["CleanedEntry"]] = relationship(
        "CleanedEntry"
    )

    # Indexes and schema configuration
    __table_args__ = (
        Index("idx_notion_syncs_user_id", "user_id"),
        Index("idx_notion_syncs_entry_id", "entry_id"),
        Index("idx_notion_syncs_status", "status"),
        Index("idx_notion_syncs_notion_page_id", "notion_page_id"),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return f"<NotionSync(id={self.id}, entry_id={self.entry_id}, status={self.status.value})>"
