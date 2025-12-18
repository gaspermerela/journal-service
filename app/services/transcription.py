"""
Transcription service for audio-to-text conversion.
Provides abstract base class and factory function.

Note: Local Whisper support has been removed. Use API-based providers
(groq, assemblyai, clarinsi_slovene_asr) instead.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from app.utils.logger import get_logger

logger = get_logger("transcription")


class TranscriptionService(ABC):
    """
    Abstract base class for transcription services.
    Allows flexibility to swap implementations (local Whisper, API, etc.)
    """

    @abstractmethod
    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        enable_diarization: bool = False,
        speaker_count: int = 1
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es') or 'auto' for detection
            beam_size: Beam size for transcription (1-10). If None, uses default.
            temperature: Temperature for transcription sampling (0.0-1.0). If None, uses default (0.0).
            model: Model to use for transcription. If None, uses the service's default model.
            enable_diarization: Enable speaker diarization to identify different speakers.
            speaker_count: Expected number of speakers (1-10). Only used if enable_diarization=True.

        Returns:
            Dict containing:
                - text: Transcribed text
                - language: Detected/used language
                - segments: List of timed segments with optional speaker labels
                - beam_size: Beam size used for transcription
                - diarization_applied: Whether speaker diarization was applied

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        pass

    @abstractmethod
    def supports_diarization(self) -> bool:
        """
        Check if this provider supports speaker diarization.

        Returns:
            True if diarization is supported, False otherwise
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes.

        Returns:
            List of ISO language codes
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the name/identifier of the model being used.

        Returns:
            Model name (e.g., 'whisper-small', 'whisper-base')
        """
        pass

    @abstractmethod
    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Get list of available models for this transcription provider.

        Returns:
            List of dicts with model information (id, name, optional metadata)
        """
        pass


def create_transcription_service(
    provider: str = "groq",
    model_name: Optional[str] = None,
    api_key: Optional[str] = None,
    endpoint_id: Optional[str] = None
) -> TranscriptionService:
    """
    Factory function to create transcription service based on provider.

    Note: Local Whisper support has been removed. Only API-based providers are supported.

    Args:
        provider: Provider name ("groq", "assemblyai", or "clarinsi_slovene_asr")
        model_name: Name of the model (e.g., 'whisper-large-v3', 'universal', 'protoverb-slovenian-asr')
        api_key: API key for cloud providers (required for groq, assemblyai, runpod)
        endpoint_id: RunPod serverless endpoint ID (required for runpod provider)

    Returns:
        TranscriptionService implementation

    Raises:
        ValueError: If provider is not supported or required params missing
    """
    provider = provider.lower()

    if provider == "groq":
        if api_key is None:
            raise ValueError("api_key is required for groq provider")
        if model_name is None:
            raise ValueError("model_name is required for groq provider")

        # Import here to avoid circular dependency and fail gracefully if groq not installed
        try:
            from app.services.transcription_groq import GroqTranscriptionService
            return GroqTranscriptionService(
                api_key=api_key,
                model=model_name
            )
        except ImportError as e:
            raise ValueError(
                f"Groq provider selected but groq package not installed. "
                f"Install with: pip install groq"
            ) from e
    elif provider == "assemblyai":
        if api_key is None:
            raise ValueError("api_key is required for assemblyai provider")
        if model_name is None:
            raise ValueError("model_name is required for assemblyai provider")

        try:
            from app.services.transcription_assemblyai import AssemblyAITranscriptionService
            from app.config import settings

            return AssemblyAITranscriptionService(
                api_key=api_key,
                model=model_name,
                poll_interval=settings.ASSEMBLYAI_POLL_INTERVAL,
                timeout=settings.ASSEMBLYAI_TIMEOUT,
                auto_delete=settings.ASSEMBLYAI_AUTO_DELETE
            )
        except ImportError as e:
            raise ValueError(
                f"AssemblyAI provider selected but httpx package not installed. "
                f"Install with: pip install httpx"
            ) from e
    elif provider == "clarinsi_slovene_asr":
        if api_key is None:
            raise ValueError("api_key is required for runpod provider")
        if endpoint_id is None:
            raise ValueError("endpoint_id is required for runpod provider")

        try:
            from app.services.transcription_runpod import RunPodTranscriptionService
            from app.config import settings

            return RunPodTranscriptionService(
                api_key=api_key,
                endpoint_id=endpoint_id,
                model=model_name or settings.RUNPOD_MODEL,
                chunk_duration_seconds=settings.RUNPOD_CHUNK_DURATION_SECONDS,
                chunk_overlap_seconds=settings.RUNPOD_CHUNK_OVERLAP_SECONDS,
                use_silence_detection=settings.RUNPOD_USE_SILENCE_DETECTION,
                max_concurrent_chunks=settings.RUNPOD_MAX_CONCURRENT_CHUNKS,
                max_retries=settings.RUNPOD_MAX_RETRIES,
                timeout=settings.RUNPOD_TIMEOUT
            )
        except ImportError as e:
            raise ValueError(
                f"clarinsi_slovene_asr provider selected but required packages not installed. "
                f"Install with: pip install httpx mutagen"
            ) from e
    else:
        raise ValueError(
            f"Unsupported transcription provider: {provider}. "
            f"Supported providers: groq, assemblyai, clarinsi_slovene_asr"
        )
