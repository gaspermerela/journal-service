"""
LLM Cleanup Service factory for creating appropriate LLM service instances.
"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.llm_cleanup_base import LLMCleanupService
from app.utils.logger import get_logger


logger = get_logger("services.llm_cleanup_factory")


def create_llm_cleanup_service(
    provider: Optional[str] = None,
    db_session: Optional[AsyncSession] = None
) -> LLMCleanupService:
    """
    Factory function to create appropriate LLM cleanup service based on provider.

    Args:
        provider: Provider name ("groq", "runpod_llm_gams"). If None, uses settings.LLM_PROVIDER
        db_session: Optional database session for prompt template lookup

    Returns:
        LLMCleanupService instance for the specified provider

    Raises:
        ValueError: If provider is not supported
    """
    if provider is None:
        provider = settings.LLM_PROVIDER

    provider = provider.lower()

    if provider == "groq":
        # Import here to avoid circular dependency and to fail gracefully if groq not installed
        try:
            from app.services.llm_cleanup_groq import GroqLLMCleanupService
            logger.info(f"Creating Groq LLM cleanup service with model: {settings.GROQ_LLM_MODEL}")
            return GroqLLMCleanupService(db_session=db_session)
        except ImportError as e:
            raise ValueError(
                f"Groq provider selected but groq package not installed. "
                f"Install with: pip install groq"
            ) from e
    elif provider == "runpod_llm_gams":
        # GaMS (Generative Model for Slovene) on RunPod serverless
        try:
            from app.services.llm_cleanup_runpod_gams import RunPodGamsLLMCleanupService
            logger.info(
                f"Creating GaMS LLM cleanup service on RunPod with model: "
                f"{settings.RUNPOD_LLM_GAMS_MODEL}"
            )
            return RunPodGamsLLMCleanupService(db_session=db_session)
        except ImportError as e:
            raise ValueError(
                f"RunPod GaMS provider selected but httpx package not installed. "
                f"Install with: pip install httpx"
            ) from e
    else:
        raise ValueError(
            f"Unsupported LLM provider: {provider}. "
            f"Supported providers: groq, runpod_llm_gams"
        )


# For backward compatibility - expose the prompts
from app.services.llm_cleanup_base import DREAM_CLEANUP_PROMPT, GENERIC_CLEANUP_PROMPT

__all__ = [
    "create_llm_cleanup_service",
    "LLMCleanupService",
    "DREAM_CLEANUP_PROMPT",
    "GENERIC_CLEANUP_PROMPT",
]
