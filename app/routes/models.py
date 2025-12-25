"""
API routes for listing available models and options.
"""
from fastapi import APIRouter, HTTPException

from app.config import settings, TRANSCRIPTION_PROVIDER_PARAMETERS, LLM_PROVIDER_PARAMETERS
from app.schemas.models import (
    LanguagesListResponse,
    ModelInfo,
    UnifiedOptionsResponse,
    ServiceOptions,
    ParameterConfig
)
from app.services.provider_registry import (
    get_transcription_service_for_provider,
    get_llm_service_for_provider,
    get_available_transcription_providers,
    get_available_llm_providers,
)
from app.utils.logger import get_logger

logger = get_logger("routes.models")

router = APIRouter(prefix="/api/v1", tags=["Models"])


@router.get("/options", response_model=UnifiedOptionsResponse)
async def get_options() -> UnifiedOptionsResponse:
    """
    Get unified options for transcription and LLM services.

    Returns available models and provider-specific parameters with constraints.
    Frontend uses this to dynamically render configuration UI.

    **No authentication required** - this endpoint is public.

    Returns:
        UnifiedOptionsResponse: Combined options for both services including:
            - provider: Current active provider (groq, assemblyai, clarin-slovene-asr, ollama)
            - available_providers: List of all configured providers
            - models: List of available models for current provider
            - parameters: Available parameters with type, min/max, default, description
    """
    try:
        # Get list of available (configured) providers
        available_transcription = get_available_transcription_providers()
        available_llm = get_available_llm_providers()

        # Create services for default providers
        transcription_service = get_transcription_service_for_provider(settings.TRANSCRIPTION_PROVIDER)
        llm_service = get_llm_service_for_provider(settings.LLM_PROVIDER)

        # Get models from services
        transcription_models = await transcription_service.list_available_models()
        llm_models = await llm_service.list_available_models()

        # Get provider-specific parameters
        transcription_params = TRANSCRIPTION_PROVIDER_PARAMETERS.get(
            settings.TRANSCRIPTION_PROVIDER,
            {}
        )
        llm_params = LLM_PROVIDER_PARAMETERS.get(
            settings.LLM_PROVIDER,
            {}
        )

        return UnifiedOptionsResponse(
            transcription=ServiceOptions(
                provider=settings.TRANSCRIPTION_PROVIDER,
                available_providers=available_transcription,
                models=[ModelInfo(**m) for m in transcription_models],
                parameters={
                    k: ParameterConfig(**v)
                    for k, v in transcription_params.items()
                }
            ),
            llm=ServiceOptions(
                provider=settings.LLM_PROVIDER,
                available_providers=available_llm,
                models=[ModelInfo(**m) for m in llm_models],
                parameters={
                    k: ParameterConfig(**v)
                    for k, v in llm_params.items()
                }
            )
        )
    except Exception as e:
        logger.error(f"Failed to fetch options: {e}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch options: {str(e)}"
        )


@router.get("/models/languages", response_model=LanguagesListResponse)
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
