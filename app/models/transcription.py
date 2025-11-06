"""
SQLAlchemy model for transcriptions table.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Boolean, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Transcription(Base):
    """
    Transcription model storing audio transcription results.

    Supports multiple transcriptions per voice entry to enable:
    - Model experimentation (base vs medium vs large)
    - Language variants
    - Retry attempts
    - Quality improvements

    Attributes:
        id: Unique identifier (UUID4)
        entry_id: Foreign key to voice_entries table
        transcribed_text: The transcription result (nullable until complete)
        status: Processing status (pending, processing, completed, failed)
        model_used: Whisper model used (e.g., "whisper-base", "whisper-large")
        language_code: Language code (e.g., "en", "auto")
        transcription_started_at: When transcription processing began
        transcription_completed_at: When transcription finished
        error_message: Error details if status is 'failed'
        is_primary: Whether this is the primary transcription to display
        created_at: Record creation time
        updated_at: Last update time
    """

    __tablename__ = "transcriptions"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key to voice_entries
    entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.voice_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Transcription data
    transcribed_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )  # Values: pending, processing, completed, failed

    model_used: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    language_code: Mapped[str] = mapped_column(
        String(10),
        nullable=False
    )

    # Timing
    transcription_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    transcription_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Error handling
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    # Primary transcription flag
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True
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

    # Relationship to VoiceEntry
    entry: Mapped["VoiceEntry"] = relationship(
        "VoiceEntry",
        back_populates="transcriptions"
    )

    # Indexes for query performance and schema configuration
    __table_args__ = (
        Index("idx_transcriptions_entry_id_is_primary", "entry_id", "is_primary"),
        Index("idx_transcriptions_status", "status"),
        Index("idx_transcriptions_created_at", "created_at"),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return (
            f"<Transcription(id={self.id}, entry_id={self.entry_id}, "
            f"status={self.status}, model={self.model_used})>"
        )
