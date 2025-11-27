"""
Schemas for model listing endpoints.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union


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


class ParameterConfig(BaseModel):
    """Configuration for a single parameter."""

    type: str = Field(..., description="Parameter type (float, int, string, etc.)")
    min: Optional[float] = Field(None, description="Minimum value (for numeric types)")
    max: Optional[float] = Field(None, description="Maximum value (for numeric types)")
    default: Union[float, int, str, None] = Field(None, description="Default value")
    description: str = Field(..., description="Parameter description")

    class Config:
        json_schema_extra = {
            "example": {
                "type": "float",
                "min": 0.0,
                "max": 2.0,
                "default": 1.0,
                "description": "Temperature for LLM sampling (0.0-2.0, higher = more creative)"
            }
        }


class ServiceOptions(BaseModel):
    """Options for a specific service (transcription or LLM)."""

    provider: str = Field(..., description="Current active provider")
    models: List[ModelInfo] = Field(..., description="Available models")
    parameters: Dict[str, ParameterConfig] = Field(..., description="Available parameters with configuration")

    class Config:
        json_schema_extra = {
            "example": {
                "provider": "groq",
                "models": [
                    {
                        "id": "llama-3.3-70b-versatile",
                        "name": "Llama 3.3 70B Versatile",
                        "owned_by": "Meta",
                        "context_window": 131072,
                        "active": True
                    }
                ],
                "parameters": {
                    "temperature": {
                        "type": "float",
                        "min": 0.0,
                        "max": 2.0,
                        "default": 1.0,
                        "description": "Temperature for LLM sampling (0.0-2.0, higher = more creative)"
                    },
                    "top_p": {
                        "type": "float",
                        "min": 0.0,
                        "max": 1.0,
                        "default": 1.0,
                        "description": "Top-p nucleus sampling (0.0-1.0)"
                    }
                }
            }
        }


class UnifiedOptionsResponse(BaseModel):
    """Unified response containing all options for transcription and LLM services."""

    transcription: ServiceOptions = Field(..., description="Transcription service options")
    llm: ServiceOptions = Field(..., description="LLM cleanup service options")

    class Config:
        json_schema_extra = {
            "example": {
                "transcription": {
                    "provider": "groq",
                    "models": [
                        {
                            "id": "whisper-large-v3",
                            "name": "Whisper Large V3",
                            "owned_by": "OpenAI",
                            "active": True
                        }
                    ],
                    "parameters": {
                        "temperature": {
                            "type": "float",
                            "min": 0.0,
                            "max": 1.0,
                            "default": 0.0,
                            "description": "Temperature for transcription sampling"
                        }
                    }
                },
                "llm": {
                    "provider": "groq",
                    "models": [
                        {
                            "id": "llama-3.3-70b-versatile",
                            "name": "Llama 3.3 70B Versatile",
                            "owned_by": "Meta",
                            "context_window": 131072,
                            "active": True
                        }
                    ],
                    "parameters": {
                        "temperature": {
                            "type": "float",
                            "min": 0.0,
                            "max": 2.0,
                            "default": 1.0,
                            "description": "Temperature for LLM sampling"
                        },
                        "top_p": {
                            "type": "float",
                            "min": 0.0,
                            "max": 1.0,
                            "default": 1.0,
                            "description": "Top-p nucleus sampling"
                        }
                    }
                }
            }
        }
