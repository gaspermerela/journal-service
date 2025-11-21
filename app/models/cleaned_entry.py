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
    Integer,
    Boolean,
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
    __table_args__ = {"schema": "journal"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    voice_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("journal.voice_entries.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    transcription_id = Column(
        UUID(as_uuid=True),
        ForeignKey("journal.transcriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("journal.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Cleanup results
    cleaned_text = Column(Text, nullable=True)
    analysis = Column(JSON, nullable=True)  # Structured data: themes, emotions, etc.
    llm_raw_response = Column(Text, nullable=True)  # Raw response from LLM before parsing

    # Processing metadata
    prompt_template_id = Column(
        Integer,
        ForeignKey("journal.prompt_templates.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    model_name = Column(String(100), nullable=False)
    status = Column(
        SQLEnum(
            CleanupStatus,
            name="cleanupstatus",
            schema="journal",
            create_constraint=False, # Don't try to create the enum type (Alembic migration already created it)
            # SQLAlchemy uses PostgreSQL's native ENUM type and sends the Python enum's .name attribute (uppercase: COMPLETED).
            # With False: SQLAlchemy treats it as a string column and we control what gets sent
            native_enum=False,
            #  This lambda extracts the .value attribute from each enum member
            #   - CleanupStatus.COMPLETED.value → "completed" (lowercase)
            #   - Without this, it would use .name → "COMPLETED" (uppercase)
            values_callable=lambda x: [e.value for e in x]
        ),
        nullable=False,
        default=CleanupStatus.PENDING,
        index=True
    )
    error_message = Column(Text, nullable=True)

    # Primary cleanup flag
    is_primary = Column(Boolean, nullable=False, default=True, index=True)

    # Timestamps
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    voice_entry = relationship("VoiceEntry", back_populates="cleaned_entries")
    transcription = relationship("Transcription", back_populates="cleaned_entries")
    user = relationship("User", back_populates="cleaned_entries")
    prompt_template = relationship("PromptTemplate", back_populates="cleaned_entries")

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
