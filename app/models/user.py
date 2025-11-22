"""
SQLAlchemy model for users table.
"""
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Index, Enum as SQLAEnum
from typing import Optional
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, Enum):
    """User role enumeration."""
    USER = "user"
    ADMIN = "admin"

if TYPE_CHECKING:
    from app.models.voice_entry import VoiceEntry
    from app.models.cleaned_entry import CleanedEntry
    from app.models.notion_sync import NotionSync
    from app.models.user_preference import UserPreference


class User(Base):
    """
    User model for authentication and authorization.

    Attributes:
        id: Unique identifier (UUID4)
        email: User's email address (unique)
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        created_at: Account creation timestamp (UTC)
        updated_at: Last update timestamp (UTC)
    """

    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    # Notion integration fields
    notion_api_key_encrypted: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True
    )

    notion_database_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    notion_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false"
    )

    notion_auto_sync: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true"
    )

    # Role
    role: Mapped[UserRole] = mapped_column(
        SQLAEnum(UserRole, name="userrole", schema="journal", values_callable=lambda obj: [e.value for e in obj]),
        nullable=False,
        default=UserRole.USER,
        server_default="user"
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
    voice_entries: Mapped[list["VoiceEntry"]] = relationship(
        "VoiceEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    cleaned_entries: Mapped[list["CleanedEntry"]] = relationship(
        "CleanedEntry",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    notion_syncs: Mapped[list["NotionSync"]] = relationship(
        "NotionSync",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    preferences: Mapped[Optional["UserPreference"]] = relationship(
        "UserPreference",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin"
    )

    # Indexes and schema configuration
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_is_active", "is_active"),
        Index("idx_users_role", "role"),
        {"schema": "journal"}
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, is_active={self.is_active})>"
