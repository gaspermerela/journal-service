"""
SQLAlchemy model for user_preferences table.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserPreference(Base):
    """
    User preferences model for storing user-specific configuration settings.

    Attributes:
        id: Unique identifier (UUID4)
        user_id: Foreign key to users table (unique - one preference record per user)
        preferred_transcription_language: Language code for Whisper transcription (default: 'auto')
        created_at: Record creation timestamp (UTC)
        updated_at: Last update timestamp (UTC)
    """

    __tablename__ = "user_preferences"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Foreign key to users
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journal.users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )

    # Transcription preferences
    preferred_transcription_language: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        default="auto",
        server_default="auto"
    )

    # LLM preferences
    preferred_llm_model: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="User's preferred LLM model for cleanup"
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
        back_populates="preferences",
        lazy="selectin"
    )

    # Indexes and schema configuration
    __table_args__ = (
        Index("idx_user_preferences_user_id", "user_id", unique=True),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return f"<UserPreference(user_id={self.user_id}, language={self.preferred_transcription_language})>"
