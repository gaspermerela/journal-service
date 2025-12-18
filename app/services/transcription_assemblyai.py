"""
AssemblyAI transcription service implementation.
Supports async upload-submit-poll-delete workflow with GDPR compliance.
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

import httpx

from app.services.transcription import TranscriptionService
from app.utils.logger import get_logger

logger = get_logger("transcription.assemblyai")

# AssemblyAI API endpoints
ASSEMBLYAI_UPLOAD_URL = "https://api.eu.assemblyai.com/v2/upload"
ASSEMBLYAI_TRANSCRIPT_URL = "https://api.eu.assemblyai.com/v2/transcript"


class AssemblyAITranscriptionService(TranscriptionService):
    """
    AssemblyAI API implementation for transcription.
    Uses 4-step async workflow: upload -> submit -> poll -> delete (GDPR).
    """

    # Polling configuration defaults
    DEFAULT_POLL_INTERVAL = 3.0  # seconds
    DEFAULT_TIMEOUT = 300  # 5 minutes max wait

    def __init__(
        self,
        api_key: str,
        model: str = "universal",
        poll_interval: float = DEFAULT_POLL_INTERVAL,
        timeout: float = DEFAULT_TIMEOUT,
        auto_delete: bool = True
    ):
        """
        Initialize AssemblyAI transcription service.

        Args:
            api_key: AssemblyAI API key
            model: Speech model (default: "universal" for 99+ languages)
            poll_interval: Seconds between status polls
            timeout: Maximum seconds to wait for transcription
            auto_delete: Auto-delete transcript after extraction (GDPR compliance)
        """
        self.api_key = api_key
        self.model = model
        self.poll_interval = poll_interval
        self.timeout = timeout
        self.auto_delete = auto_delete

        # 1-hour cache for available models (following Groq pattern)
        self._models_cache: Optional[list[Dict[str, Any]]] = None
        self._models_cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=1)

        logger.info(f"AssemblyAITranscriptionService initialized with model={model}, auto_delete={auto_delete}")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for API requests."""
        return {"Authorization": self.api_key}

    async def _upload_audio(self, audio_path: Path) -> str:
        """
        Step 1: Upload audio file to AssemblyAI.

        Args:
            audio_path: Path to local audio file

        Returns:
            upload_url: URL of uploaded audio for transcription

        Raises:
            RuntimeError: If upload fails
        """
        logger.info(f"Uploading audio file to AssemblyAI: {audio_path.name}")

        async with httpx.AsyncClient(timeout=60.0) as client:
            with open(audio_path, "rb") as f:
                response = await client.post(
                    ASSEMBLYAI_UPLOAD_URL,
                    headers=self._get_headers(),
                    content=f.read()
                )

            if response.status_code != 200:
                raise RuntimeError(
                    f"AssemblyAI upload failed: {response.status_code} - {response.text}"
                )

            upload_url = response.json()["upload_url"]
            logger.info(f"Audio uploaded successfully: {audio_path.name}")
            return upload_url

    async def _submit_transcription(
        self,
        audio_url: str,
        language: str,
        speech_model: str,
        enable_diarization: bool = False,
        speaker_count: int = 1
    ) -> str:
        """
        Step 2: Submit transcription job.

        Args:
            audio_url: URL of uploaded audio
            language: Language code or "auto"
            speech_model: AssemblyAI speech model name
            enable_diarization: Enable speaker diarization
            speaker_count: Expected number of speakers (only used if enable_diarization=True)

        Returns:
            transcript_id: ID for polling status

        Raises:
            RuntimeError: If submission fails
        """
        logger.info(
            f"Submitting transcription job: model={speech_model}, language={language}, "
            f"diarization={enable_diarization}, speakers={speaker_count}"
        )

        payload: Dict[str, Any] = {
            "audio_url": audio_url,
            "speech_model": speech_model,
        }

        # AssemblyAI requires language_code (no auto-detect support)
        # If "auto" is passed, default to "en_us"
        if language and language.lower() != "auto":
            payload["language_code"] = language
        else:
            payload["language_code"] = "en_us"
            logger.warning(
                "AssemblyAI does not support auto language detection, defaulting to en_us"
            )

        # Add speaker diarization settings if enabled
        if enable_diarization:
            payload["speaker_labels"] = True
            if speaker_count > 1:
                payload["speakers_expected"] = speaker_count
            logger.info(f"Speaker diarization enabled with {speaker_count} expected speakers")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ASSEMBLYAI_TRANSCRIPT_URL,
                headers={
                    **self._get_headers(),
                    "Content-Type": "application/json"
                },
                json=payload
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"AssemblyAI submit failed: {response.status_code} - {response.text}"
                )

            data = response.json()
            transcript_id = data["id"]
            logger.info(f"Transcription job submitted: id={transcript_id}")
            return transcript_id

    async def _poll_transcription(self, transcript_id: str) -> Dict[str, Any]:
        """
        Step 3: Poll for transcription completion.

        Args:
            transcript_id: ID of transcription job

        Returns:
            Completed transcription response

        Raises:
            RuntimeError: If transcription fails or times out
        """
        logger.info(f"Polling transcription status: id={transcript_id}")

        start_time = asyncio.get_event_loop().time()
        poll_url = f"{ASSEMBLYAI_TRANSCRIPT_URL}/{transcript_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            while True:
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > self.timeout:
                    raise RuntimeError(
                        f"AssemblyAI transcription timed out after {self.timeout}s"
                    )

                response = await client.get(poll_url, headers=self._get_headers())

                if response.status_code != 200:
                    raise RuntimeError(
                        f"AssemblyAI poll failed: {response.status_code} - {response.text}"
                    )

                data = response.json()
                status = data["status"]

                if status == "completed":
                    logger.info(f"Transcription completed: id={transcript_id}")
                    return data
                elif status == "error":
                    error_msg = data.get("error", "Unknown error")
                    raise RuntimeError(f"AssemblyAI transcription failed: {error_msg}")

                # Still processing - wait before next poll
                logger.debug(
                    f"Transcription in progress: id={transcript_id}, "
                    f"status={status}, elapsed={elapsed:.1f}s"
                )
                await asyncio.sleep(self.poll_interval)

    async def _delete_transcript(self, transcript_id: str) -> None:
        """
        Step 4: Delete transcript from AssemblyAI (GDPR compliance).

        Called immediately after extracting result.
        Logged but does not raise - deletion failure shouldn't break workflow.

        Args:
            transcript_id: ID of transcript to delete
        """
        delete_url = f"{ASSEMBLYAI_TRANSCRIPT_URL}/{transcript_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(delete_url, headers=self._get_headers())

                if response.status_code == 200:
                    logger.info(f"Transcript deleted for GDPR compliance: id={transcript_id}")
                else:
                    logger.warning(
                        f"Failed to delete transcript (non-critical): "
                        f"id={transcript_id}, status={response.status_code}"
                    )
        except Exception as e:
            logger.warning(
                f"GDPR deletion failed (non-critical): id={transcript_id}, error={str(e)}"
            )

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
        Transcribe audio using AssemblyAI 4-step workflow.
        Blocks until transcription completes (like Groq).

        Args:
            audio_path: Path to audio file
            language: Language code or "auto" for auto-detection
            beam_size: Not supported by AssemblyAI (logged, ignored)
            temperature: Not supported by AssemblyAI (logged, ignored)
            model: Speech model override (default: instance model)
            enable_diarization: Enable speaker diarization to identify different speakers
            speaker_count: Expected number of speakers (1-10). Only used if enable_diarization=True.

        Returns:
            Dict with transcription result including diarization_applied flag

        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If any step fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        effective_model = model if model else self.model

        # Log warnings for unsupported parameters
        if beam_size is not None:
            logger.warning(
                f"beam_size parameter not supported by AssemblyAI (provided: {beam_size})"
            )
        if temperature is not None:
            logger.warning(
                f"temperature parameter not supported by AssemblyAI (provided: {temperature})"
            )

        logger.info(
            f"Starting AssemblyAI transcription: file={audio_path.name}, "
            f"language={language}, model={effective_model}, "
            f"diarization={enable_diarization}, speakers={speaker_count}"
        )

        transcript_id = None
        try:
            # Step 1: Upload audio
            upload_url = await self._upload_audio(audio_path)

            # Step 2: Submit transcription job (with diarization if enabled)
            transcript_id = await self._submit_transcription(
                audio_url=upload_url,
                language=language,
                speech_model=effective_model,
                enable_diarization=enable_diarization,
                speaker_count=speaker_count
            )

            # Step 3: Poll until complete
            result = await self._poll_transcription(transcript_id)

            # Extract text and language
            transcribed_text = result.get("text", "")
            detected_language = result.get("language_code", language)

            # Extract segments - prefer utterances (with speaker labels) if diarization was requested
            segments = []
            diarization_applied = False

            if enable_diarization and "utterances" in result and result["utterances"]:
                # Use utterances (contains speaker labels)
                segments = self._utterances_to_segments(result["utterances"])
                diarization_applied = True
                logger.info(f"Extracted {len(segments)} speaker-labeled segments from utterances")
            elif "words" in result and result["words"]:
                # Fall back to word-level segments (no speaker labels)
                segments = self._words_to_segments(result["words"])

            logger.info(
                f"AssemblyAI transcription completed: file={audio_path.name}, "
                f"language={detected_language}, length={len(transcribed_text)} chars, "
                f"diarization_applied={diarization_applied}"
            )

            return {
                "text": transcribed_text,
                "language": detected_language,
                "segments": segments,
                "beam_size": None,  # Not supported
                "temperature": None,  # Not supported
                "diarization_applied": diarization_applied,
            }

        except Exception as e:
            logger.error(
                f"AssemblyAI transcription failed: file={audio_path.name}, error={str(e)}",
                exc_info=True
            )
            raise RuntimeError(f"AssemblyAI transcription failed: {str(e)}") from e

        finally:
            # Step 4: GDPR delete (if auto_delete is enabled)
            if transcript_id and self.auto_delete:
                await self._delete_transcript(transcript_id)

    def _words_to_segments(self, words: list[Dict]) -> list[Dict[str, Any]]:
        """
        Convert AssemblyAI word-level data to segment format.
        Groups words into natural segments based on timing gaps.

        Args:
            words: List of word objects from AssemblyAI

        Returns:
            List of segment dicts with id, start, end, text
        """
        if not words:
            return []

        segments = []
        current_segment_words = []
        segment_id = 0
        gap_threshold_ms = 1000  # 1 second gap creates new segment

        for i, word in enumerate(words):
            current_segment_words.append(word)

            # Check if this should end the segment
            is_last = (i == len(words) - 1)
            if not is_last:
                next_word = words[i + 1]
                gap = next_word.get("start", 0) - word.get("end", 0)
                should_split = gap > gap_threshold_ms
            else:
                should_split = True

            if should_split and current_segment_words:
                segment = {
                    "id": segment_id,
                    "start": current_segment_words[0].get("start", 0) / 1000.0,
                    "end": current_segment_words[-1].get("end", 0) / 1000.0,
                    "text": " ".join(w.get("text", "") for w in current_segment_words)
                }
                segments.append(segment)
                segment_id += 1
                current_segment_words = []

        return segments

    def _utterances_to_segments(self, utterances: list[Dict]) -> list[Dict[str, Any]]:
        """
        Convert AssemblyAI utterances (with speaker labels) to segment format.

        AssemblyAI returns speaker labels as letters (A, B, C...).
        We convert these to "Speaker 1", "Speaker 2", etc.

        Args:
            utterances: List of utterance objects from AssemblyAI with speaker labels

        Returns:
            List of segment dicts with id, start, end, text, speaker
        """
        if not utterances:
            return []

        # Build speaker mapping (A -> Speaker 1, B -> Speaker 2, etc.)
        speaker_map: Dict[str, str] = {}
        speaker_counter = 1

        segments = []
        for i, utterance in enumerate(utterances):
            speaker_letter = utterance.get("speaker", "")

            # Map speaker letter to "Speaker N" format
            if speaker_letter and speaker_letter not in speaker_map:
                speaker_map[speaker_letter] = f"Speaker {speaker_counter}"
                speaker_counter += 1

            speaker_label = speaker_map.get(speaker_letter, None)

            segment = {
                "id": i,
                "start": utterance.get("start", 0) / 1000.0,  # Convert ms to seconds
                "end": utterance.get("end", 0) / 1000.0,
                "text": utterance.get("text", "").strip(),
                "speaker": speaker_label,
            }
            segments.append(segment)

        logger.debug(f"Mapped {len(speaker_map)} unique speakers: {speaker_map}")
        return segments

    def get_supported_languages(self) -> list[str]:
        """
        Get supported language codes.
        AssemblyAI does NOT support auto language detection.
        Returns a curated list of 10 supported languages.
        """
        return [
            "en",  # English (defaults to en_us)
            "en_us",  # English (US)
            "en_uk",  # English (UK)
            "sl",  # Slovenian
            "de",  # German
            "fr",  # French
            "es",  # Spanish
            "it",  # Italian
            "hr",  # Croatian
            "sr",  # Serbian
        ]

    def get_model_name(self) -> str:
        """
        Get model name in format: assemblyai-{model}
        """
        return f"assemblyai-{self.model}"

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Return available AssemblyAI speech models.
        Uses 1-hour cache (following Groq pattern).

        AssemblyAI models are currently static, but we maintain
        the cache pattern for future API integration.
        """
        # Check cache
        if self._models_cache is not None and self._models_cache_timestamp is not None:
            if datetime.now() - self._models_cache_timestamp < self._cache_ttl:
                logger.debug("Returning cached AssemblyAI models")
                return self._models_cache

        # AssemblyAI speech models (hardcoded for now)
        models = [
            {
                "id": "universal",
                "name": "Universal (99+ languages)",
                "description": "Best for multilingual content, automatic language detection",
                "languages": "99+"
            }
        ]

        # Update cache
        self._models_cache = models
        self._models_cache_timestamp = datetime.now()

        logger.info(f"Cached {len(models)} AssemblyAI models (cache TTL: 1 hour)")
        return models

    def supports_diarization(self) -> bool:
        """
        AssemblyAI supports native speaker diarization via speaker_labels.

        Returns:
            True - diarization is supported
        """
        return True
