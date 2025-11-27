"""
Transcription service for audio-to-text conversion.
Provides abstract base class and concrete implementations.
"""
import asyncio
import torch
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
        beam_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es') or 'auto' for detection
            beam_size: Beam size for transcription (1-10). If None, uses default.

        Returns:
            Dict containing:
                - text: Transcribed text
                - language: Detected/used language
                - segments: Optional list of timed segments
                - beam_size: Beam size used for transcription

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
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


class WhisperLocalService(TranscriptionService):
    """
    Local Whisper model implementation for transcription.
    Runs Whisper model directly using CPU/GPU.

    Note: Uses a lock to ensure only one transcription runs at a time,
    as Whisper's KV caching is not thread-safe.
    """

    def __init__(
        self,
        model: Any,
        model_name: str,
        device: str = "cpu",
        num_threads: int = 10
    ):
        """
        Initialize Whisper local service.

        Args:
            model: Loaded Whisper model instance
            model_name: Name of the model (e.g., 'small', 'base', 'medium')
            device: Device to use ('cpu' or 'cuda')
            num_threads: Number of CPU threads for PyTorch
        """
        self.model = model
        self.model_name = model_name
        self.device = device
        self.num_threads = num_threads

        # Lock to prevent concurrent access to the model
        # Whisper's KV caching uses forward hooks that are not thread-safe
        self._transcription_lock = asyncio.Lock()

        # Set PyTorch thread count for CPU optimization
        if device == "cpu":
            torch.set_num_threads(num_threads)
            logger.info(f"Set PyTorch threads to {num_threads} for CPU inference")

        logger.info(f"WhisperLocalService initialized with device={device}")

    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using local Whisper model.

        Args:
            audio_path: Path to audio file
            language: Language code or 'auto' for automatic detection
            beam_size: Beam size for transcription (1-10). If None, uses default based on model size.

        Returns:
            Dict with transcription result (includes beam_size used)

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(
            f"Starting transcription: file={audio_path.name}, "
            f"language={language}, device={self.device}"
        )

        try:
            # Acquire lock to ensure only one transcription runs at a time
            # This prevents race conditions in Whisper's KV caching mechanism
            if self._transcription_lock.locked():
                logger.info(
                    f"Transcription queued (another transcription in progress): {audio_path.name}"
                )

            async with self._transcription_lock:
                logger.info(f"Transcription processing started: {audio_path.name}")

                # Run Whisper transcription in thread pool to avoid blocking event loop
                # Whisper's transcribe() is CPU-intensive and synchronous
                result = await asyncio.to_thread(
                    self._transcribe_sync,
                    str(audio_path),
                    language,
                    beam_size
                )

            logger.info(
                f"Transcription completed: file={audio_path.name}, "
                f"text_length={len(result['text'])} chars"
            )

            return result

        except Exception as e:
            logger.error(
                f"Transcription failed: file={audio_path.name}, error={str(e)}",
                exc_info=True
            )
            raise RuntimeError(f"Transcription failed: {str(e)}") from e

    def _transcribe_sync(self, audio_path: str, language: str, beam_size: Optional[int] = None) -> Dict[str, Any]:
        """
        Synchronous transcription (runs in thread pool).

        Args:
            audio_path: Path to audio file as string
            language: Language code or 'auto'
            beam_size: Beam size for transcription (1-10). If None, uses config default.

        Returns:
            Dict with transcription result (includes beam_size used)
        """
        # Import config here to get default beam size
        from app.config import settings

        # Configure transcription options based on device
        # FP16 enabled for GPU (faster), disabled for CPU (required)
        use_fp16 = self.device == "cuda"

        # Use provided beam_size or fall back to config default
        # Previous logic used model-based defaults (5 for large, 1 for others)
        # Now we respect user's choice or use config default
        if beam_size is None:
            beam_size = settings.WHISPER_DEFAULT_BEAM_SIZE

        # For large models, still use best_of=2 for better quality
        is_large_model = "large" in self.model_name.lower()

        transcribe_options = {
            "fp16": use_fp16,
            "language": None if language == "auto" else language,
            "task": "transcribe",  # vs "translate"
            "beam_size": beam_size,
            "best_of": 1 if not is_large_model else 2,  # Better for large models
        }

        logger.info(
            "Transcription options configured",
            fp16=use_fp16,
            beam_size=beam_size,
            model=self.model_name,
            device=self.device
        )

        # Perform transcription
        result = self.model.transcribe(audio_path, **transcribe_options)

        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": result.get("segments", []),
            "beam_size": beam_size,  # Include beam_size in result
        }

    def get_supported_languages(self) -> list[str]:
        """
        Get list of languages supported by Whisper.

        Returns:
            List of ISO language codes
        """
        # Whisper supports 99 languages
        # https://github.com/openai/whisper#available-models-and-languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
            "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
            "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
            "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
            "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
            "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
            "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
            "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
            "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
            "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su", "auto"
        ]

    def get_model_name(self) -> str:
        """
        Get the name of the Whisper model being used.

        Returns:
            Model name with 'whisper-' prefix (e.g., 'whisper-small')
        """
        return f"whisper-{self.model_name}"

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Return hardcoded list of available local Whisper models.

        Returns:
            List of dicts with model information
        """
        return [
            {"id": "tiny", "name": "Whisper Tiny", "size": "~75MB", "speed": "very fast"},
            {"id": "base", "name": "Whisper Base", "size": "~150MB", "speed": "fast"},
            {"id": "small", "name": "Whisper Small", "size": "~500MB", "speed": "moderate"},
            {"id": "medium", "name": "Whisper Medium", "size": "~1.5GB", "speed": "slow"},
            {"id": "large", "name": "Whisper Large", "size": "~3GB", "speed": "very slow"},
            {"id": "large-v3", "name": "Whisper Large v3", "size": "~3GB", "speed": "very slow"}
        ]


def create_transcription_service(
    provider: str = "whisper",
    model: Optional[Any] = None,
    model_name: Optional[str] = None,
    device: str = "cpu",
    num_threads: int = 10,
    api_key: Optional[str] = None
) -> TranscriptionService:
    """
    Factory function to create transcription service based on provider.

    Args:
        provider: Provider name ("whisper" for local, "groq" for API)
        model: Loaded Whisper model instance (only for local whisper)
        model_name: Name of the model (e.g., 'large-v3')
        device: Device to use for local whisper ('cpu' or 'cuda')
        num_threads: Number of CPU threads for local whisper
        api_key: API key for Groq (required if provider is "groq")

    Returns:
        TranscriptionService implementation

    Raises:
        ValueError: If provider is not supported or required params missing
    """
    provider = provider.lower()

    if provider == "whisper":
        if model is None or model_name is None:
            raise ValueError("model and model_name are required for whisper provider")
        return WhisperLocalService(
            model=model,
            model_name=model_name,
            device=device,
            num_threads=num_threads
        )
    elif provider == "groq":
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
    else:
        raise ValueError(
            f"Unsupported transcription provider: {provider}. "
            f"Supported providers: whisper, groq"
        )
