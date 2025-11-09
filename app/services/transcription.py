"""
Transcription service for audio-to-text conversion.
Provides abstract base class and concrete implementations.
"""
import asyncio
import torch
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any
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
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file to text.

        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es') or 'auto' for detection

        Returns:
            Dict containing:
                - text: Transcribed text
                - language: Detected/used language
                - segments: Optional list of timed segments

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
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using local Whisper model.

        Args:
            audio_path: Path to audio file
            language: Language code or 'auto' for automatic detection

        Returns:
            Dict with transcription result

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
                    language
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

    def _transcribe_sync(self, audio_path: str, language: str) -> Dict[str, Any]:
        """
        Synchronous transcription (runs in thread pool).

        Args:
            audio_path: Path to audio file as string
            language: Language code or 'auto'

        Returns:
            Dict with transcription result
        """
        # Configure transcription options
        transcribe_options = {
            "fp16": False,  # Use fp32 for CPU (required for CPU inference)
            "language": None if language == "auto" else language,
            "task": "transcribe",  # vs "translate"
            "beam_size": 1,  # Faster, slightly less accurate
            "best_of": 1,  # Faster decoding
        }

        # Perform transcription
        result = self.model.transcribe(audio_path, **transcribe_options)

        return {
            "text": result["text"].strip(),
            "language": result.get("language", language),
            "segments": result.get("segments", []),
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


def create_transcription_service(
    model: Any,
    model_name: str,
    device: str = "cpu",
    num_threads: int = 10
) -> TranscriptionService:
    """
    Factory function to create transcription service.
    Makes it easy to swap implementations later.

    Args:
        model: Loaded model instance
        model_name: Name of the model (e.g., 'small', 'base')
        device: Device to use ('cpu' or 'cuda')
        num_threads: Number of CPU threads

    Returns:
        TranscriptionService implementation
    """
    return WhisperLocalService(
        model=model,
        model_name=model_name,
        device=device,
        num_threads=num_threads
    )
