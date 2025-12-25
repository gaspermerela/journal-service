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
    # Slovenian ASR with multiple RunPod endpoints (different diarization backends)
    "clarin-slovene-asr": {
        "required_settings": ["RUNPOD_API_KEY"],
        "description": "Slovenian ASR with PROTOVERB model",
    "runpods": {
            "nfa": {
                "endpoint_setting": "SLOVENE_ASR_NFA_ENDPOINT_ID",
                "description": "NeMo ClusteringDiarizer + NFA alignment"
            },
            "mms": {
                "endpoint_setting": "SLOVENE_ASR_MMS_ENDPOINT_ID",
                "description": "NeMo ClusteringDiarizer + MMS alignment"
            },
            "pyannote": {
                "endpoint_setting": "SLOVENE_ASR_PYANNOTE_ENDPOINT_ID",
                "description": "pyannote 3.1 diarization (best quality)"
            }
        }
    },
    "noop": {
        "required_settings": [],  # Always available for testing
        "description": "NoOp (test provider)"
    }
}

LLM_PROVIDERS: Dict[str, Dict[str, Any]] = {
    "groq": {
        "required_settings": ["GROQ_API_KEY"],
        "description": "Groq API (LLaMA models)"
    },
    "runpod_llm_gams": {
        "required_settings": ["RUNPOD_API_KEY", "RUNPOD_LLM_GAMS_ENDPOINT_ID"],
        "description": "GaMS Slovenian LLM on RunPod"
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

    For providers with multiple models (e.g., clarin-slovene-asr), returns True
    if the base requirements are met AND at least one model endpoint is configured.

    Args:
        provider: Provider name (e.g., "groq", "assemblyai", "clarin-slovene-asr")

    Returns:
        True if provider is valid and configured, False otherwise
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        return False

    provider_config = TRANSCRIPTION_PROVIDERS[provider]
    required = provider_config["required_settings"]

    # Check base requirements
    if not _check_settings_configured(required):
        return False

    # For providers with multiple RunPod endpoints, check if at least one is configured
    if "runpods" in provider_config:
        for runpod_config in provider_config["runpods"].values():
            endpoint_setting = runpod_config.get("endpoint_setting")
            if endpoint_setting and _check_settings_configured([endpoint_setting]):
                return True
        # No RunPod endpoints configured
        return False

    return True


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

    For providers with models, includes a note if no model endpoints are configured.

    Args:
        provider: Provider name

    Returns:
        List of missing setting names (empty if all configured or provider invalid)
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        return []

    provider_config = TRANSCRIPTION_PROVIDERS[provider]
    missing = []

    # Check base requirements
    for setting_name in provider_config["required_settings"]:
        value = getattr(settings, setting_name, None)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(setting_name)

    # For providers with RunPod endpoints, check if any are configured
    if "runpods" in provider_config:
        has_any_endpoint = False
        for runpod_config in provider_config["runpods"].values():
            endpoint_setting = runpod_config.get("endpoint_setting")
            if endpoint_setting:
                value = getattr(settings, endpoint_setting, None)
                if value and (not isinstance(value, str) or value.strip()):
                    has_any_endpoint = True
                    break
        if not has_any_endpoint:
            # List all possible endpoint settings
            endpoint_settings = [
                r["endpoint_setting"]
                for r in provider_config["runpods"].values()
                if "endpoint_setting" in r
            ]
            missing.append(f"At least one of: {', '.join(endpoint_settings)}")

    return missing


def get_available_runpods_for_provider(provider: str) -> List[Dict[str, Any]]:
    """
    Get list of available (configured) RunPod endpoints for a transcription provider.

    For providers with multiple RunPod endpoints (e.g., clarin-slovene-asr), returns
    only endpoints that are configured.

    Args:
        provider: Provider name

    Returns:
        List of runpod dicts with 'id' and 'description' keys
    """
    provider = provider.lower()

    if provider not in TRANSCRIPTION_PROVIDERS:
        return []

    provider_config = TRANSCRIPTION_PROVIDERS[provider]

    # If no runpods defined, return empty (provider uses single endpoint)
    if "runpods" not in provider_config:
        return []

    available = []
    for runpod_id, runpod_config in provider_config["runpods"].items():
        endpoint_setting = runpod_config.get("endpoint_setting")
        if endpoint_setting and _check_settings_configured([endpoint_setting]):
            available.append({
                "id": runpod_id,
                "description": runpod_config.get("description", "")
            })

    return available


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


def get_transcription_service_for_provider(
    provider: str,
    model: Optional[str] = None
) -> TranscriptionService:
    """
    Create a transcription service instance for the specified provider.

    Uses settings to get API keys and configuration.

    Args:
        provider: Provider name (e.g., "groq", "assemblyai", "clarin-slovene-asr")
        model: Model name for providers with multiple models (e.g., "pyannote" for clarin-slovene-asr).
               If not specified, uses the first available model.

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

    logger.info(f"Creating transcription service for provider: {provider}", model=model)

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
    elif provider == "clarin-slovene-asr":
        # Resolve model to RunPod endpoint_id
        provider_config = TRANSCRIPTION_PROVIDERS[provider]
        runpods_config = provider_config.get("runpods", {})

        # If no model specified, use first available RunPod
        if not model:
            available_runpods = get_available_runpods_for_provider(provider)
            if not available_runpods:
                raise ValueError(
                    f"No RunPod endpoints configured for provider '{provider}'. "
                    f"Configure at least one endpoint ID."
                )
            model = available_runpods[0]["id"]
            logger.info(f"No model specified, using default RunPod: {model}")

        model = model.lower()
        if model not in runpods_config:
            available = ", ".join(runpods_config.keys())
            raise ValueError(
                f"Unknown model '{model}' for provider '{provider}'. "
                f"Available: {available}"
            )

        runpod_config = runpods_config[model]
        endpoint_setting = runpod_config["endpoint_setting"]
        endpoint_id = getattr(settings, endpoint_setting, None)

        if not endpoint_id:
            raise ValueError(
                f"RunPod '{model}' is not configured for provider '{provider}'. "
                f"Missing setting: {endpoint_setting}"
            )

        return create_transcription_service(
            provider="clarin-slovene-asr",
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=endpoint_id,
            variant=model
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
    provider = requested_provider or settings.DEFAULT_TRANSCRIPTION_PROVIDER
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
    provider = requested_provider or settings.DEFAULT_LLM_PROVIDER
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
