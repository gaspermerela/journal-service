"""
PromptTemplate model for managing LLM cleanup prompts.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Index,
)
from sqlalchemy.orm import relationship

from app.database import Base


class PromptTemplate(Base):
    """
    Represents a versioned prompt template for LLM cleanup.

    Each entry type can have multiple prompt versions, with one marked as active.
    This allows for easy A/B testing and prompt iteration without code changes.
    """
    __tablename__ = "prompt_templates"
    __table_args__ = (
        Index(
            'ix_prompt_templates_active',
            'entry_type',
            'is_active',
            postgresql_where=Column('is_active') == True
        ),
        {"schema": "journal"}
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    entry_type = Column(String(50), nullable=False, index=True)
    prompt_text = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=False)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    cleaned_entries = relationship("CleanedEntry", back_populates="prompt_template")

    def __repr__(self) -> str:
        return (
            f"<PromptTemplate(id={self.id}, "
            f"name='{self.name}', "
            f"entry_type='{self.entry_type}', "
            f"version={self.version}, "
            f"is_active={self.is_active})>"
        )

    @property
    def is_valid(self) -> bool:
        """Check if the prompt template has required fields."""
        return (
            self.prompt_text is not None
            and len(self.prompt_text.strip()) > 0
            and "{transcription_text}" in self.prompt_text
        )
