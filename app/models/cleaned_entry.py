"""
CleanedEntry model for LLM-processed transcription text.
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column,
    String,
    Text,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


class CleanupStatus(str, Enum):
    """Status of LLM cleanup processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class CleanedEntry(Base):
    """
    Represents an LLM-cleaned version of a transcription.

    Contains the cleaned text and extracted analysis (themes, emotions, etc.)
    from processing the original transcription through a local LLM.
    """
    __tablename__ = "cleaned_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voice_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("voice_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transcription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transcriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Cleanup results
    cleaned_text = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True)  # Structured data: themes, emotions, etc.

    # Processing metadata
    prompt_used = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    status = Column(
        SQLEnum(CleanupStatus, name="cleanupstatus"),
        nullable=False,
        default=CleanupStatus.PENDING,
        index=True
    )
    error_message = Column(Text, nullable=True)

    # Timestamps
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    voice_entry = relationship("VoiceEntry", back_populates="cleaned_entries")
    transcription = relationship("Transcription", back_populates="cleaned_entries")
    user = relationship("User", back_populates="cleaned_entries")

    def __repr__(self) -> str:
        return (
            f"<CleanedEntry(id={self.id}, "
            f"transcription_id={self.transcription_id}, "
            f"status={self.status}, "
            f"model={self.model_name})>"
        )

    @property
    def processing_time_seconds(self) -> Optional[float]:
        """Calculate processing time in seconds if available."""
        if self.processing_started_at and self.processing_completed_at:
            delta = self.processing_completed_at - self.processing_started_at
            return delta.total_seconds()
        return None
