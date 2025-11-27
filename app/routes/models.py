"""
API routes for listing available models.
"""
from fastapi import APIRouter, HTTPException, Request
from app.schemas.models import ModelsListResponse, LanguagesListResponse, ModelInfo
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("routes.models")

router = APIRouter(prefix="/api/v1/models", tags=["Models"])


@router.get("/transcription", response_model=ModelsListResponse)
async def list_transcription_models(request: Request):
    """
    List available transcription models for the current provider.

    Returns models based on TRANSCRIPTION_PROVIDER setting:
    - `groq`: Fetches from Groq API dynamically
    - `whisper`: Returns local Whisper models (hardcoded)

    **No authentication required** - this endpoint is public.

    Returns:
        ModelsListResponse: Provider name and list of available models
    """
    transcription_service = request.app.state.transcription_service

    try:
        models = await transcription_service.list_available_models()

        return ModelsListResponse(
            provider=settings.TRANSCRIPTION_PROVIDER,
            models=[ModelInfo(**model) for model in models]
        )
    except Exception as e:
        logger.error(f"Failed to fetch transcription models: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch transcription models: {str(e)}"
        )


@router.get("/llm", response_model=ModelsListResponse)
async def list_llm_models(request: Request):
    """
    List available LLM models for the current provider.

    Returns models based on LLM_PROVIDER setting:
    - `groq`: Fetches from Groq API dynamically (excludes whisper models)
    - `ollama`: Returns common Ollama models (hardcoded)

    **No authentication required** - this endpoint is public.

    Returns:
        ModelsListResponse: Provider name and list of available models
    """
    llm_service = request.app.state.llm_cleanup_service

    try:
        models = await llm_service.list_available_models()

        return ModelsListResponse(
            provider=settings.LLM_PROVIDER,
            models=[ModelInfo(**model) for model in models]
        )
    except Exception as e:
        logger.error(f"Failed to fetch LLM models: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch LLM models: {str(e)}"
        )


@router.get("/languages", response_model=LanguagesListResponse)
async def list_supported_languages():
    """
    List supported transcription languages.

    Returns all languages supported by Whisper (99+ languages + 'auto' for auto-detection).
    This list is the same regardless of transcription provider (Whisper or Groq), as both
    use the same underlying Whisper models.

    **No authentication required** - this endpoint is public.

    Returns:
        LanguagesListResponse: List of language codes and total count
    """
    from app.utils.language_validator import get_supported_languages

    try:
        languages = get_supported_languages()

        return LanguagesListResponse(
            languages=languages,
            count=len(languages)
        )
    except Exception as e:
        logger.error(f"Failed to fetch supported languages: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch supported languages: {str(e)}"
        )
