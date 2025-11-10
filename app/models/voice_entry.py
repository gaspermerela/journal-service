"""
SQLAlchemy model for voice entries table.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional
from sqlalchemy import String, Text, DateTime, Index, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.transcription import Transcription
    from app.models.user import User


class VoiceEntry(Base):
    """
    Voice entry model storing audio file metadata.

    Attributes:
        id: Unique identifier (UUID4)
        user_id: Foreign key to users table
        original_filename: Original name of uploaded file
        saved_filename: UUID-based filename on disk
        file_path: Absolute path to saved file
        entry_type: Type of voice entry (dream, journal, meeting, note, etc.)
        uploaded_at: Upload timestamp (UTC)
        created_at: Record creation time
        updated_at: Last update time
    """

    __tablename__ = "voice_entries"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key to user
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.users.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for backward compatibility
        index=True
    )

    # File metadata
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    saved_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    file_path: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # Entry metadata
    entry_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="dream",
        server_default="dream",
        index=True
    )

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

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
    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="voice_entries",
        lazy="selectin"
    )

    transcriptions: Mapped[list["Transcription"]] = relationship(
        "Transcription",
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes for query performance and schema configuration
    __table_args__ = (
        Index("idx_voice_entries_uploaded_at", "uploaded_at"),
        Index("idx_voice_entries_entry_type", "entry_type"),
        Index("idx_voice_entries_user_id", "user_id"),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return f"<VoiceEntry(id={self.id}, entry_type={self.entry_type}, original_filename={self.original_filename})>"
