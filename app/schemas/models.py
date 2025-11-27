"""
Schemas for model listing endpoints.
"""
from pydantic import BaseModel, Field
from typing import List, Optional


class ModelInfo(BaseModel):
    """Information about a single model."""

    id: str = Field(..., description="Model identifier")
    name: str = Field(..., description="Human-readable model name")
    owned_by: Optional[str] = Field(None, description="Model owner/provider")
    context_window: Optional[int] = Field(None, description="Context window size")
    size: Optional[str] = Field(None, description="Model size (for local models)")
    speed: Optional[str] = Field(None, description="Speed classification (for local models)")
    active: Optional[bool] = Field(None, description="Whether model is active")


class ModelsListResponse(BaseModel):
    """Response for model listing endpoints."""

    provider: str = Field(..., description="Current provider (groq, whisper, ollama)")
    models: List[ModelInfo] = Field(..., description="Available models")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "groq",
                "models": [
                    {
                        "id": "whisper-large-v3",
                        "name": "whisper-large-v3",
                        "owned_by": "OpenAI",
                        "context_window": 448,
                        "active": True
                    }
                ]
            }
        }


class LanguagesListResponse(BaseModel):
    """Response for languages listing endpoint."""

    languages: List[str] = Field(..., description="List of supported language codes")
    count: int = Field(..., description="Total number of supported languages")

    class Config:
        json_schema_extra = {
            "example": {
                "languages": ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"],
                "count": 100
            }
        }
