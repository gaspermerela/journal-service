"""
SQLAlchemy model for dream entries table.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.transcription import Transcription


class DreamEntry(Base):
    """
    Dream entry model storing audio file metadata.

    Attributes:
        id: Unique identifier (UUID4)
        original_filename: Original name of uploaded file
        saved_filename: UUID-based filename on disk
        file_path: Absolute path to saved file
        uploaded_at: Upload timestamp (UTC)
        created_at: Record creation time
        updated_at: Last update time
    """

    __tablename__ = "dream_entries"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
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
    transcriptions: Mapped[list["Transcription"]] = relationship(
        "Transcription",
        back_populates="entry",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Indexes for query performance and schema configuration
    __table_args__ = (
        Index("idx_dream_entries_uploaded_at", "uploaded_at"),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return f"<DreamEntry(id={self.id}, original_filename={self.original_filename})>"
