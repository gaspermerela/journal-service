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
    preferred_llm_model: Optional[str] = Field(
        default=None,
        description="Preferred LLM model in format 'provider-model' (e.g., 'ollama-llama3.2:3b', 'groq-llama-3.3-70b-versatile')"
    )
    encryption_enabled: bool = Field(
        default=True,
        description="Whether to encrypt voice entries at rest (enabled by default, opt-out)"
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
    preferred_llm_model: Optional[str] = Field(
        None,
        description="Preferred LLM model in format 'provider-model' (e.g., 'ollama-llama3.2:3b', 'groq-llama-3.3-70b-versatile')"
    )
    encryption_enabled: Optional[bool] = Field(
        None,
        description="Whether to encrypt voice entries at rest (enabled by default, opt-out)"
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
    preferred_llm_model: Optional[str] = Field(
        default=None,
        description="Preferred LLM model"
    )
    encryption_enabled: bool = Field(
        default=True,
        description="Whether to encrypt voice entries at rest (enabled by default)"
    )

    @field_validator('preferred_transcription_language')
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        if not validate_language_code(v):
            raise ValueError(f"Unsupported language code: '{v}'")
        return v
