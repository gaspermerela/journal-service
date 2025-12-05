"""
SQLAlchemy model for Data Encryption Keys (DEKs).

Stores encrypted DEKs for the envelope encryption pattern.
Each DEK is associated with a VoiceEntry and used to encrypt all related data
(audio file, transcriptions, cleaned entries) for that entry.

GDPR Compliance:
    Setting deleted_at and zeroing encrypted_dek renders the associated
    data permanently unrecoverable (cryptographic erasure).
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DateTime, Integer, LargeBinary, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, DB_SCHEMA


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.voice_entry import VoiceEntry


class DataEncryptionKey(Base):
    """
    Data Encryption Key model for envelope encryption.

    Each VoiceEntry gets one DEK that encrypts all its associated data:
    - The audio file
    - All transcriptions
    - All cleaned entries

    Envelope Encryption Pattern:
        Master Key → KEK (per-user) → DEK (per-voice-entry) → Data

    Benefits of one DEK per VoiceEntry:
    - Fewer KMS calls (1 per entry vs 3+)
    - Simpler deletion (one DEK covers entire entry chain)
    - Supports multiple transcriptions/cleanups per entry

    GDPR Deletion:
        To perform cryptographic erasure:
        1. Set deleted_at timestamp
        2. Overwrite encrypted_dek with random bytes
        3. Commit transaction
        This makes all data for the VoiceEntry permanently unrecoverable.

    Attributes:
        id: Unique identifier (UUID4)
        user_id: Owner user's UUID (FK to users)
        voice_entry_id: Associated VoiceEntry's UUID (FK, unique)
        encrypted_dek: DEK encrypted with user's KEK
        encryption_version: Provider version string (e.g., "local-v1")
        key_version: Version number for key rotation tracking
        created_at: Key creation timestamp (UTC)
        rotated_at: Last key rotation timestamp (UTC)
        deleted_at: Soft deletion timestamp for GDPR compliance (UTC)

    Indexes:
        - user_id: For user-scoped queries
        - voice_entry_id: Unique (one DEK per VoiceEntry)
        - deleted_at: Partial index for active keys
    """

    __tablename__ = "data_encryption_keys"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Owner relationship
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{DB_SCHEMA}.users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # VoiceEntry association (one DEK per VoiceEntry)
    voice_entry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(f"{DB_SCHEMA}.voice_entries.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        doc="VoiceEntry this DEK protects (and all its transcriptions/cleaned entries)",
    )

    # Encrypted DEK (binary data)
    encrypted_dek: Mapped[bytes] = mapped_column(
        LargeBinary,
        nullable=False,
    )

    # Version tracking for provider migration
    encryption_version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="KEK provider version (e.g., 'local-v1', 'aws-kms-v1')",
    )

    key_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
        doc="Key rotation version number",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    rotated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last key rotation timestamp",
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="GDPR deletion timestamp - key is destroyed when set",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="data_encryption_keys",
        lazy="selectin",
    )

    voice_entry: Mapped["VoiceEntry"] = relationship(
        "VoiceEntry",
        back_populates="data_encryption_key",
        lazy="selectin",
    )

    # Table constraints and indexes
    __table_args__ = (
        # Partial index for active (non-deleted) keys
        Index(
            "idx_dek_active",
            "voice_entry_id",
            postgresql_where=(deleted_at.is_(None)),
        ),
        {"schema": DB_SCHEMA},
    )

    def __repr__(self) -> str:
        return (
            f"<DataEncryptionKey id={self.id} "
            f"voice_entry_id={self.voice_entry_id} "
            f"version={self.encryption_version} "
            f"deleted={self.deleted_at is not None}>"
        )

    @property
    def is_deleted(self) -> bool:
        """Check if this DEK has been deleted (GDPR erasure)."""
        return self.deleted_at is not None

    @property
    def is_active(self) -> bool:
        """Check if this DEK is active (not deleted)."""
        return self.deleted_at is None
