"""
RunPod transcription service implementation.
Uses PROTOVERB Slovenian ASR model on RunPod serverless GPU with NLP pipeline.
Supports client-side audio chunking for long recordings (1h+).

Pipeline: Audio -> ASR (PROTOVERB) -> Punctuation (optional) -> Denormalization (optional)
"""
import asyncio
import base64
import random
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List

import httpx

from app.services.transcription import TranscriptionService
from app.utils.audio_chunking import AudioChunker, AudioChunk
from app.utils.logger import get_logger

logger = get_logger("transcription.runpod")


class RunPodTranscriptionService(TranscriptionService):
    """
    RunPod API implementation for Slovenian transcription using PROTOVERB model.
    Includes optional punctuation and denormalization pipeline.
    Supports client-side audio chunking for long recordings.
    """

    # Supported languages (Slovenian only)
    SUPPORTED_LANGUAGES = ["sl", "sl-SI", "auto"]

    # Chunk threshold - audio longer than this will be chunked
    CHUNK_THRESHOLD_SECONDS = 300  # 5 minutes

    # Valid denormalization styles
    VALID_DENORMALIZE_STYLES = ["default", "technical", "everyday"]

    def __init__(
        self,
        api_key: str,
        endpoint_id: str,
        model: str = "rsdo-slovenian-asr",
        chunk_duration_seconds: int = 240,
        chunk_overlap_seconds: int = 5,
        use_silence_detection: bool = True,
        max_concurrent_chunks: int = 3,
        max_retries: int = 3,
        timeout: int = 300,
        punctuate: bool = True,
        denormalize: bool = True,
        denormalize_style: str = "default"
    ):
        """
        Initialize RunPod transcription service.

        Args:
            api_key: RunPod API key
            endpoint_id: RunPod serverless endpoint ID
            model: Model name for identification (default: protoverb-slovenian-asr)
            chunk_duration_seconds: Target duration for each chunk (default: 4 min)
            chunk_overlap_seconds: Overlap between chunks (default: 5s)
            use_silence_detection: Use silence detection for chunk boundaries
            max_concurrent_chunks: Max parallel chunk transcriptions
            max_retries: Max retry attempts on failure
            timeout: Max seconds per chunk request
            punctuate: Enable punctuation & capitalization (default: True)
            denormalize: Enable text denormalization (default: True)
            denormalize_style: Denormalization style - default, technical, everyday
        """
        if not api_key:
            raise ValueError("api_key is required for RunPod provider")
        if not endpoint_id:
            raise ValueError("endpoint_id is required for RunPod provider")

        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.model = model
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_concurrent_chunks = max_concurrent_chunks
        self.use_silence_detection = use_silence_detection

        # NLP pipeline defaults
        self.punctuate = punctuate
        self.denormalize = denormalize
        self.denormalize_style = denormalize_style

        # Validate denormalize_style
        if denormalize_style not in self.VALID_DENORMALIZE_STYLES:
            logger.warning(
                f"Invalid denormalize_style '{denormalize_style}', using 'default'"
            )
            self.denormalize_style = "default"

        # Initialize audio chunker
        self._chunker = AudioChunker(
            chunk_duration_seconds=chunk_duration_seconds,
            overlap_seconds=chunk_overlap_seconds
        )

        # RunPod API base URL
        self._base_url = f"https://api.runpod.ai/v2/{endpoint_id}"

        logger.info(
            f"RunPodTranscriptionService initialized",
            endpoint_id=endpoint_id,
            model=model,
            chunk_duration_s=chunk_duration_seconds,
            max_concurrent=max_concurrent_chunks,
            punctuate=punctuate,
            denormalize=denormalize,
            denormalize_style=self.denormalize_style
        )

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers for RunPod API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def transcribe_audio(
        self,
        audio_path: Path,
        language: str = "sl",
        beam_size: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        punctuate: Optional[bool] = None,
        denormalize: Optional[bool] = None,
        denormalize_style: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio file using RunPod PROTOVERB service with NLP pipeline.

        For long audio (>5 min), automatically chunks the audio,
        transcribes in parallel, and reassembles the results.

        Args:
            audio_path: Path to audio file (WAV recommended, 16kHz mono)
            language: Language code (only 'sl', 'sl-SI', or 'auto' accepted)
            beam_size: Not supported (ignored with warning)
            temperature: Not supported (ignored with warning)
            model: Not supported (uses fixed PROTOVERB model, ignored with warning)
            punctuate: Override default punctuation setting (optional)
            denormalize: Override default denormalization setting (optional)
            denormalize_style: Override default denormalization style (optional)

        Returns:
            Dict containing:
                - text: Final processed text (after NLP pipeline)
                - raw_text: Original ASR output (before NLP pipeline)
                - language: "sl" (always Slovenian)
                - segments: Empty list (not supported)
                - beam_size: None (not supported)
                - temperature: None (not supported)
                - pipeline: List of processing steps applied
                - model_version: Model version identifier
                - chunking_metadata: Optional dict with chunking stats

        Raises:
            FileNotFoundError: If audio file doesn't exist
            ValueError: If language is not Slovenian
            RuntimeError: If transcription fails
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Validate language
        if language not in self.SUPPORTED_LANGUAGES:
            raise ValueError(
                f"RunPod PROTOVERB only supports Slovenian. "
                f"Got: '{language}', supported: {self.SUPPORTED_LANGUAGES}"
            )

        # Log warnings for unsupported parameters
        if beam_size is not None:
            logger.warning("beam_size parameter not supported by RunPod PROTOVERB (ignored)")
        if temperature is not None:
            logger.warning("temperature parameter not supported by RunPod PROTOVERB (ignored)")
        if model and model != self.model:
            logger.warning(
                f"model parameter not supported by RunPod PROTOVERB (ignored). "
                f"Using fixed model: {self.model}"
            )

        # Resolve NLP pipeline options (use instance defaults if not overridden)
        do_punctuate = punctuate if punctuate is not None else self.punctuate
        do_denormalize = denormalize if denormalize is not None else self.denormalize
        style = denormalize_style if denormalize_style is not None else self.denormalize_style

        # Validate denormalize_style
        if style not in self.VALID_DENORMALIZE_STYLES:
            logger.warning(f"Invalid denormalize_style '{style}', using 'default'")
            style = "default"

        logger.info(
            "Starting RunPod transcription",
            audio_path=str(audio_path),
            language=language,
            punctuate=do_punctuate,
            denormalize=do_denormalize,
            denormalize_style=style
        )

        # Build NLP options dict
        nlp_options = {
            "punctuate": do_punctuate,
            "denormalize": do_denormalize,
            "denormalize_style": style
        }

        # Check if chunking is needed
        if self._chunker.needs_chunking(audio_path, self.CHUNK_THRESHOLD_SECONDS):
            return await self._transcribe_with_chunking(audio_path, nlp_options)
        else:
            return await self._transcribe_single(audio_path, nlp_options)

    async def _transcribe_single(
        self,
        audio_path: Path,
        nlp_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transcribe a single audio file without chunking.

        Args:
            audio_path: Path to audio file
            nlp_options: Dict with punctuate, denormalize, denormalize_style

        Returns:
            Transcription result dict
        """
        logger.info("Transcribing single audio file (no chunking)", audio_path=str(audio_path))

        # Read and encode audio
        audio_bytes = audio_path.read_bytes()
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

        # Call RunPod with NLP options
        result = await self._call_runpod_with_retry({
            "audio_base64": audio_base64,
            "filename": audio_path.name,
            "punctuate": nlp_options["punctuate"],
            "denormalize": nlp_options["denormalize"],
            "denormalize_style": nlp_options["denormalize_style"]
        })

        text = result.get("text", "").strip()
        raw_text = result.get("raw_text", text)  # Fallback to text if raw_text not provided
        pipeline = result.get("pipeline", ["asr"])
        model_version = result.get("model_version", "unknown")

        logger.info(
            "Single transcription completed",
            text_length=len(text),
            pipeline=pipeline,
            processing_time=result.get("processing_time")
        )

        return {
            "text": text,
            "raw_text": raw_text,
            "language": "sl",
            "segments": [],
            "beam_size": None,
            "temperature": None,
            "pipeline": pipeline,
            "model_version": model_version
        }

    async def _transcribe_with_chunking(
        self,
        audio_path: Path,
        nlp_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Transcribe long audio with chunking.

        Splits audio into chunks, transcribes in parallel, and reassembles.
        NLP processing is applied per-chunk.

        Args:
            audio_path: Path to audio file
            nlp_options: Dict with punctuate, denormalize, denormalize_style

        Returns:
            Transcription result dict with chunking_metadata
        """
        logger.info("Transcribing with chunking", audio_path=str(audio_path))

        # Create temp directory for chunks
        with tempfile.TemporaryDirectory(prefix="runpod_chunks_") as temp_dir:
            output_dir = Path(temp_dir)

            # Chunk audio
            chunks = self._chunker.chunk_audio(
                audio_path,
                output_dir=output_dir,
                use_silence_detection=self.use_silence_detection
            )

            logger.info(f"Created {len(chunks)} chunks for transcription")

            # Transcribe chunks in parallel
            results = await self._transcribe_chunks_parallel(chunks, nlp_options)

            # Reassemble transcriptions
            combined_text = self._reassemble_transcriptions(results)
            combined_raw_text = self._reassemble_transcriptions(results, use_raw=True)

            # Get chunking metadata
            chunking_metadata = self._chunker.get_chunk_metadata(chunks)
            chunking_metadata["successful_chunks"] = len(results)
            chunking_metadata["total_chunks"] = len(chunks)

            # Get pipeline from first result (should be same for all)
            pipeline = results[0].get("pipeline", ["asr"]) if results else ["asr"]
            model_version = results[0].get("model_version", "unknown") if results else "unknown"

            logger.info(
                "Chunked transcription completed",
                num_chunks=len(chunks),
                successful_chunks=len(results),
                combined_text_length=len(combined_text),
                pipeline=pipeline
            )

            return {
                "text": combined_text,
                "raw_text": combined_raw_text,
                "language": "sl",
                "segments": [],
                "beam_size": None,
                "temperature": None,
                "pipeline": pipeline,
                "model_version": model_version,
                "chunking_metadata": chunking_metadata
            }

    async def _transcribe_chunks_parallel(
        self,
        chunks: List[AudioChunk],
        nlp_options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Transcribe multiple chunks in parallel with concurrency limit.

        Args:
            chunks: List of AudioChunk objects
            nlp_options: Dict with punctuate, denormalize, denormalize_style

        Returns:
            List of successful transcription results (sorted by chunk index)

        Raises:
            RuntimeError: If all chunks fail
        """
        semaphore = asyncio.Semaphore(self.max_concurrent_chunks)
        failed_chunks: List[int] = []

        async def process_chunk(chunk: AudioChunk) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    logger.info(f"Processing chunk {chunk.index + 1}/{len(chunks)}")

                    # Read and encode chunk
                    audio_bytes = chunk.path.read_bytes()
                    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

                    result = await self._call_runpod_with_retry({
                        "audio_base64": audio_base64,
                        "filename": chunk.path.name,
                        "punctuate": nlp_options["punctuate"],
                        "denormalize": nlp_options["denormalize"],
                        "denormalize_style": nlp_options["denormalize_style"]
                    })

                    return {
                        "chunk_index": chunk.index,
                        "text": result.get("text", "").strip(),
                        "raw_text": result.get("raw_text", "").strip(),
                        "processing_time": result.get("processing_time"),
                        "pipeline": result.get("pipeline", ["asr"]),
                        "model_version": result.get("model_version", "unknown"),
                        "start_time_ms": chunk.start_time_ms,
                        "end_time_ms": chunk.end_time_ms
                    }

                except Exception as e:
                    logger.error(
                        f"Chunk {chunk.index} failed",
                        chunk_index=chunk.index,
                        error=str(e)
                    )
                    failed_chunks.append(chunk.index)
                    return None

        # Process all chunks
        tasks = [process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)

        # Filter successful results
        successful = [r for r in results if r is not None]

        if not successful:
            raise RuntimeError(
                f"All {len(chunks)} chunks failed to transcribe. "
                f"Failed chunk indices: {failed_chunks}"
            )

        if failed_chunks:
            logger.warning(
                f"{len(failed_chunks)} of {len(chunks)} chunks failed",
                failed_indices=failed_chunks
            )

        # Sort by chunk index
        return sorted(successful, key=lambda r: r["chunk_index"])

    def _reassemble_transcriptions(
        self,
        results: List[Dict[str, Any]],
        use_raw: bool = False
    ) -> str:
        """
        Reassemble chunk transcriptions into final text.

        Handles overlap deduplication by joining with single space.
        Future enhancement: smarter deduplication based on overlap content.

        Args:
            results: List of chunk transcription results (sorted by index)
            use_raw: If True, use raw_text instead of text

        Returns:
            Combined transcription text
        """
        field = "raw_text" if use_raw else "text"
        texts = [r.get(field, r.get("text", "")) for r in results if r.get(field) or r.get("text")]
        return " ".join(texts)

    async def _call_runpod_with_retry(
        self,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Call RunPod API with exponential backoff retry.

        Args:
            input_data: Input payload for RunPod handler

        Returns:
            Output from RunPod handler

        Raises:
            RuntimeError: If all retries fail
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                return await self._call_runpod_sync(input_data)

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(
                        f"RunPod timeout, retrying in {wait_time:.1f}s",
                        attempt=attempt + 1,
                        max_retries=self.max_retries
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("RunPod timeout, max retries exceeded")

            except httpx.HTTPStatusError as e:
                last_error = e
                status_code = e.response.status_code

                if status_code == 429:
                    # Rate limited - respect Retry-After header
                    retry_after = int(e.response.headers.get("Retry-After", 5))
                    logger.warning(f"RunPod rate limited, waiting {retry_after}s")
                    await asyncio.sleep(retry_after)

                elif status_code >= 500:
                    # Server error - retry with backoff
                    if attempt < self.max_retries - 1:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"RunPod server error {status_code}, retrying in {wait_time}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"RunPod server error {status_code}, max retries exceeded")
                else:
                    # Client error - don't retry
                    raise RuntimeError(
                        f"RunPod request failed: {status_code} - {e.response.text}"
                    ) from e

            except Exception as e:
                last_error = e
                logger.error(f"Unexpected error calling RunPod: {e}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    break

        raise RuntimeError(
            f"RunPod transcription failed after {self.max_retries} attempts: {last_error}"
        )

    async def _call_runpod_sync(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make synchronous call to RunPod /runsync endpoint.

        Args:
            input_data: Input payload for handler

        Returns:
            Output from handler

        Raises:
            httpx.TimeoutException: On timeout
            httpx.HTTPStatusError: On HTTP error
            RuntimeError: On job failure
        """
        payload = {"input": input_data}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self._base_url}/runsync",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()

            result = response.json()

            status = result.get("status")
            if status == "COMPLETED":
                return result.get("output", {})
            elif status == "FAILED":
                error = result.get("error", "Unknown error")
                raise RuntimeError(f"RunPod job failed: {error}")
            else:
                raise RuntimeError(f"Unexpected RunPod status: {status}")

    def get_supported_languages(self) -> list[str]:
        """
        Get list of supported language codes.
        PROTOVERB model only supports Slovenian.

        Returns:
            List with 'sl', 'sl-SI', and 'auto' (auto defaults to Slovenian)
        """
        return self.SUPPORTED_LANGUAGES.copy()

    def get_model_name(self) -> str:
        """
        Get the name/identifier of the model being used.

        Returns:
            Model name with 'clarinsi_slovene_asr-' prefix
        """
        return f"clarinsi_slovene_asr-{self.model}"

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Get list of available models for this provider.

        Returns:
            List with PROTOVERB model info
        """
        return [
            {
                "id": "protoverb-slovenian-asr",
                "name": "PROTOVERB Slovenian ASR",
                "description": "PROTOVERB-ASR-E2E 1.0 with punctuation & denormalization pipeline",
                "language": "sl",
                "size": "~820MB (ASR + Punctuator models)",
                "wer": "~5% (9.8% improvement over RSDO 2.0)",
                "features": ["punctuation", "denormalization"],
                "pipeline_options": {
                    "punctuate": "Add punctuation and capitalization",
                    "denormalize": "Convert numbers, dates, times to written form",
                    "denormalize_style": "Formatting style: default, technical, everyday"
                }
            }
        ]
