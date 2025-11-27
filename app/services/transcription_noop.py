"""
NoOp Transcription Service for testing.
Returns mock data without calling any actual transcription service.
"""
from pathlib import Path
from typing import Dict, Any, Optional

from app.services.transcription import TranscriptionService
from app.utils.logger import get_logger


logger = get_logger("services.transcription_noop")


class NoOpTranscriptionService(TranscriptionService):
    """No-operation transcription service for testing."""

    def __init__(self, model_name: str = "noop-whisper-test"):
        self.model_name = model_name
        logger.info(f"NoOpTranscriptionService initialized with model={model_name}")

    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Return mock transcription without calling any service.

        Args:
            audio_path: Path to audio file
            language: Language code
            beam_size: Beam size (ignored for NoOp)
            temperature: Temperature (ignored for NoOp)

        Returns:
            Dict with mock transcription data
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(f"NoOp transcription called for file={audio_path.name}, language={language}")

        return {
            "text": f"[NoOp Transcription] This is a test transcription for {audio_path.name}",
            "language": language if language != "auto" else "en",
            "segments": [],
            "beam_size": beam_size
        }

    def get_supported_languages(self) -> list[str]:
        """Return list of supported languages."""
        return ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh", "sl", "hr", "sr"]

    def get_model_name(self) -> str:
        """Return model name."""
        return self.model_name

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """Return mock list of available models for testing."""
        return [
            {"id": "noop-whisper-test", "name": "NoOp Test Model"}
        ]
