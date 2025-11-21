"""
Pydantic schemas for user preferences management.
"""
from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.utils.language_validator import validate_language_code


class UserPreferencesResponse(BaseModel):
    """
    Schema for user preferences in responses.
    """
    id: UUID
    user_id: UUID
    preferred_transcription_language: str = Field(
        default="auto",
        description="Language code for transcription (e.g., 'en', 'es', 'sl') or 'auto' for automatic detection"
    )
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserPreferencesUpdate(BaseModel):
    """
    Schema for updating user preferences.
    Only includes fields that can be modified.
    """
    preferred_transcription_language: Optional[str] = Field(
        None,
        description="Language code for transcription (e.g., 'en', 'es', 'sl') or 'auto' for automatic detection"
    )

    @field_validator('preferred_transcription_language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """
        Validate that the language code is supported by Whisper.

        Args:
            v: Language code to validate

        Returns:
            Validated language code

        Raises:
            ValueError: If language code is not supported
        """
        if v is not None and not validate_language_code(v):
            raise ValueError(
                f"Unsupported language code: '{v}'. "
                f"Must be a valid ISO 639-1 language code or 'auto'."
            )
        return v


class UserPreferencesCreate(BaseModel):
    """
    Schema for creating user preferences.
    Used internally when creating default preferences for new users.
    """
    user_id: UUID
    preferred_transcription_language: str = Field(
        default="auto",
        description="Language code for transcription"
    )

    @field_validator('preferred_transcription_language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        if not validate_language_code(v):
            raise ValueError(f"Unsupported language code: '{v}'")
        return v
