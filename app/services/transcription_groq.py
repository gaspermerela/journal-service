"""
Groq API transcription service implementation.
"""
from pathlib import Path
from typing import Dict, Any, Optional

from groq import AsyncGroq

from app.services.transcription import TranscriptionService
from app.utils.logger import get_logger

logger = get_logger("transcription.groq")


class GroqTranscriptionService(TranscriptionService):
    """
    Groq API implementation for transcription using Whisper models.
    Uses Groq's cloud-hosted Whisper API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "whisper-large-v3"
    ):
        """
        Initialize Groq transcription service.

        Args:
            api_key: Groq API key
            model: Groq Whisper model name (default: whisper-large-v3)
        """
        self.api_key = api_key
        self.model = model
        self.client = AsyncGroq(api_key=api_key)

        logger.info(f"GroqTranscriptionService initialized with model={model}")

    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "en",
        beam_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using Groq's Whisper API.

        Args:
            audio_path: Path to audio file
            language: Language code or 'auto' for automatic detection
            beam_size: Not used for Groq API (Groq doesn't expose beam_size control)

        Returns:
            Dict with transcription result

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.info(
            f"Starting Groq transcription: file={audio_path.name}, "
            f"language={language}, model={self.model}"
        )

        try:
            # Read audio file
            with open(audio_path, "rb") as audio_file:
                # Call Groq transcription API
                # Note: Groq API doesn't support beam_size parameter
                transcription_params = {
                    "file": (audio_path.name, audio_file),
                    "model": self.model,
                    "response_format": "verbose_json",  # Get detailed response with segments
                }

                # Only add language if not "auto"
                if language and language.lower() != "auto":
                    transcription_params["language"] = language

                response = await self.client.audio.transcriptions.create(**transcription_params)

            # Extract data from response
            # Groq's response structure matches OpenAI's Whisper API
            transcribed_text = response.text
            detected_language = getattr(response, "language", language)

            # Extract segments if available
            segments = []
            if hasattr(response, "segments") and response.segments:
                segments = [
                    {
                        "id": seg.get("id") if isinstance(seg, dict) else seg.id,
                        "start": seg.get("start") if isinstance(seg, dict) else seg.start,
                        "end": seg.get("end") if isinstance(seg, dict) else seg.end,
                        "text": seg.get("text") if isinstance(seg, dict) else seg.text
                    }
                    for seg in response.segments
                ]

            logger.info(
                f"Groq transcription completed: file={audio_path.name}, "
                f"language={detected_language}, length={len(transcribed_text)} chars"
            )

            return {
                "text": transcribed_text,
                "language": detected_language,
                "segments": segments,
                "beam_size": None  # Groq doesn't expose beam_size
            }

        except Exception as e:
            logger.error(
                f"Groq transcription failed: file={audio_path.name}, error={str(e)}",
                exc_info=True
            )
            raise RuntimeError(f"Groq transcription failed: {str(e)}") from e

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes for Groq Whisper.
        Groq uses the same Whisper models as OpenAI, so supports the same 99+ languages.

        Returns:
            List of ISO language codes (returns common subset for brevity)
        """
        # Groq's Whisper supports the same languages as OpenAI's Whisper
        # Returning a common subset - full list is 99+ languages
        return [
            "auto",  # Auto-detect
            "en",  # English
            "es",  # Spanish
            "fr",  # French
            "de",  # German
            "it",  # Italian
            "pt",  # Portuguese
            "ru",  # Russian
            "ja",  # Japanese
            "ko",  # Korean
            "zh",  # Chinese
            "ar",  # Arabic
            "hi",  # Hindi
            "sl",  # Slovenian
            "hr",  # Croatian
            "sr",  # Serbian
            # ... and 80+ more languages
        ]

    def get_model_name(self) -> str:
        """
        Get the model name in format: groq-{model}

        Returns:
            Model name string (e.g., "groq-whisper-large-v3")
        """
        return f"groq-{self.model}"
