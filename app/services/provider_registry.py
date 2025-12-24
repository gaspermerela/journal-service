"""
Provider Registry for transcription and LLM cleanup services.

Provides centralized validation and factory functions for per-request provider selection.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.transcription import TranscriptionService, create_transcription_service
from app.services.llm_cleanup import LLMCleanupService, create_llm_cleanup_service
from app.utils.logger import get_logger


logger = get_logger("services.provider_registry")


# Provider definitions with required settings
TRANSCRIPTION_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "groq": {
        "required_settings": ["GROQ_API_KEY"],
        "description": "Groq API (Whisper large-v3)"
    },
    "assemblyai": {
        "required_settings": ["ASSEMBLYAI_API_KEY"],
        "description": "AssemblyAI API"
    },
    # Slovenian ASR pipelines with diarization support
    "clarin-slovene-asr-nfa": {
        "required_settings": ["RUNPOD_API_KEY", "SLOVENE_ASR_NFA_ENDPOINT_ID"],
        "description": "Slovenian ASR with NeMo diarization + NFA alignment"
    },
    "clarin-slovene-asr-mms": {
        "required_settings": ["RUNPOD_API_KEY", "SLOVENE_ASR_MMS_ENDPOINT_ID"],
        "description": "Slovenian ASR with NeMo diarization + MMS alignment"
    },
    "clarin-slovene-asr-pyannote": {
        "required_settings": ["RUNPOD_API_KEY", "SLOVENE_ASR_PYANNOTE_ENDPOINT_ID"],
        "description": "Slovenian ASR with pyannote 3.1 diarization (best quality)"
    },
    "noop": {
        "required_settings": [],  # Always available for testing
        "description": "NoOp (test provider)"
    }
}

LLM_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "ollama": {
        "required_settings": [],  # Ollama just needs OLLAMA_BASE_URL which has a default
        "description": "Ollama (local LLM)"
    },
    "groq": {
        "required_settings": ["GROQ_API_KEY"],
        "description": "Groq API (LLaMA models)"
    },
    "noop": {
        "required_settings": [],  # Always available for testing
        "description": "NoOp (test provider)"
    }
}


def _check_settings_configured(required_settings: List[str]) -> bool:
    """
    Check if all required settings have non-empty values.

    Args:
        required_settings: List of setting names to check

    Returns:
        True if all settings are configured, False otherwise
    """
    for setting_name in required_settings:
        value = getattr(settings, setting_name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            return False
    return True


def is_transcription_provider_configured(provider: str) -> bool:
    """
    Check if a transcription provider has all required settings configured.

    Args:
        provider: Provider name (e.g., "groq", "assemblyai", "clarin-slovene-asr-pyannote")

    Returns:
        True if provider is valid and configured, False otherwise
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        return False

    required = TRANSCRIPTION_PROVIDERS[provider]["required_settings"]
    return _check_settings_configured(required)


def is_llm_provider_configured(provider: str) -> bool:
    """
    Check if an LLM provider has all required settings configured.

    Args:
        provider: Provider name (e.g., "ollama", "groq")

    Returns:
        True if provider is valid and configured, False otherwise
    """
    provider = provider.lower()

    if provider not in LLM_PROVIDERS:
        return False

    required = LLM_PROVIDERS[provider]["required_settings"]
    return _check_settings_configured(required)


def get_missing_settings_for_transcription_provider(provider: str) -> List[str]:
    """
    Get list of missing settings for a transcription provider.

    Args:
        provider: Provider name

    Returns:
        List of missing setting names (empty if all configured or provider invalid)
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        return []

    missing = []
    for setting_name in TRANSCRIPTION_PROVIDERS[provider]["required_settings"]:
        value = getattr(settings, setting_name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(setting_name)

    return missing


def get_missing_settings_for_llm_provider(provider: str) -> List[str]:
    """
    Get list of missing settings for an LLM provider.

    Args:
        provider: Provider name

    Returns:
        List of missing setting names (empty if all configured or provider invalid)
    """
    provider = provider.lower()

    if provider not in LLM_PROVIDERS:
        return []

    missing = []
    for setting_name in LLM_PROVIDERS[provider]["required_settings"]:
        value = getattr(settings, setting_name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(setting_name)

    return missing


def get_transcription_service_for_provider(provider: str) -> TranscriptionService:
    """
    Create a transcription service instance for the specified provider.

    Uses settings to get API keys and configuration.

    Args:
        provider: Provider name (e.g., "groq", "assemblyai", "clarin-slovene-asr-pyannote")

    Returns:
        TranscriptionService instance

    Raises:
        ValueError: If provider is not supported or not configured
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        available = ", ".join(TRANSCRIPTION_PROVIDERS.keys())
        raise ValueError(
            f"Unknown transcription provider: '{provider}'. "
            f"Available providers: {available}"
        )

    if not is_transcription_provider_configured(provider):
        missing = get_missing_settings_for_transcription_provider(provider)
        raise ValueError(
            f"Transcription provider '{provider}' is not configured. "
            f"Missing settings: {', '.join(missing)}"
        )

    logger.info(f"Creating transcription service for provider: {provider}")

    if provider == "groq":
        return create_transcription_service(
            provider="groq",
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_TRANSCRIPTION_MODEL
        )
    elif provider == "assemblyai":
        return create_transcription_service(
            provider="assemblyai",
            api_key=settings.ASSEMBLYAI_API_KEY,
            model_name=settings.ASSEMBLYAI_MODEL
        )
    elif provider == "clarin-slovene-asr-nfa":
        return create_transcription_service(
            provider="clarin-slovene-asr",
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=settings.SLOVENE_ASR_NFA_ENDPOINT_ID,
            variant="nfa"
        )
    elif provider == "clarin-slovene-asr-mms":
        return create_transcription_service(
            provider="clarin-slovene-asr",
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=settings.SLOVENE_ASR_MMS_ENDPOINT_ID,
            variant="mms"
        )
    elif provider == "clarin-slovene-asr-pyannote":
        return create_transcription_service(
            provider="clarin-slovene-asr",
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID,
            variant="pyannote"
        )
    elif provider == "noop":
        from app.services.transcription_noop import NoOpTranscriptionService
        return NoOpTranscriptionService(model_name="noop-whisper-test")
    else:
        # Should not reach here due to earlier check
        raise ValueError(f"Unsupported provider: {provider}")


def get_llm_service_for_provider(
    provider: str,
    db_session: Optional[AsyncSession] = None
) -> LLMCleanupService:
    """
    Create an LLM cleanup service instance for the specified provider.

    Uses settings to get API keys and configuration.

    Args:
        provider: Provider name (e.g., "ollama", "groq")
        db_session: Optional database session for prompt template lookup

    Returns:
        LLMCleanupService instance

    Raises:
        ValueError: If provider is not supported or not configured
    """
    provider = provider.lower()

    if provider not in LLM_PROVIDERS:
        available = ", ".join(LLM_PROVIDERS.keys())
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available providers: {available}"
        )

    if not is_llm_provider_configured(provider):
        missing = get_missing_settings_for_llm_provider(provider)
        raise ValueError(
            f"LLM provider '{provider}' is not configured. "
            f"Missing settings: {', '.join(missing)}"
        )

    logger.info(f"Creating LLM service for provider: {provider}")

    if provider == "noop":
        from app.services.llm_cleanup_noop import NoOpLLMCleanupService
        return NoOpLLMCleanupService()

    return create_llm_cleanup_service(provider=provider, db_session=db_session)


def get_available_transcription_providers() -> List[str]:
    """
    Get list of transcription providers that are configured and available.

    Returns:
        List of available provider names
    """
    return [
        provider for provider in TRANSCRIPTION_PROVIDERS.keys()
        if is_transcription_provider_configured(provider)
    ]


def get_available_llm_providers() -> List[str]:
    """
    Get list of LLM providers that are configured and available.

    Returns:
        List of available provider names
    """
    return [
        provider for provider in LLM_PROVIDERS.keys()
        if is_llm_provider_configured(provider)
    ]


def get_effective_transcription_provider(requested_provider: Optional[str]) -> str:
    """
    Get the effective transcription provider, falling back to default if not specified.

    Args:
        requested_provider: Provider requested by client, or None for default

    Returns:
        Effective provider name

    Raises:
        ValueError: If provider is not valid or not configured
    """
    provider = requested_provider or settings.TRANSCRIPTION_PROVIDER
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        available = ", ".join(TRANSCRIPTION_PROVIDERS.keys())
        raise ValueError(
            f"Unknown transcription provider: '{provider}'. "
            f"Available providers: {available}"
        )

    if not is_transcription_provider_configured(provider):
        missing = get_missing_settings_for_transcription_provider(provider)
        raise ValueError(
            f"Transcription provider '{provider}' is not configured. "
            f"Missing settings: {', '.join(missing)}"
        )

    return provider


def get_effective_llm_provider(requested_provider: Optional[str]) -> str:
    """
    Get the effective LLM provider, falling back to default if not specified.

    Args:
        requested_provider: Provider requested by client, or None for default

    Returns:
        Effective provider name

    Raises:
        ValueError: If provider is not valid or not configured
    """
    provider = requested_provider or settings.LLM_PROVIDER
    provider = provider.lower()

    if provider not in LLM_PROVIDERS:
        available = ", ".join(LLM_PROVIDERS.keys())
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available providers: {available}"
        )

    if not is_llm_provider_configured(provider):
        missing = get_missing_settings_for_llm_provider(provider)
        raise ValueError(
            f"LLM provider '{provider}' is not configured. "
            f"Missing settings: {', '.join(missing)}"
        )

    return provider
