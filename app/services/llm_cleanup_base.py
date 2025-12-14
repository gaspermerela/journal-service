"""
Abstract base class for LLM cleanup services.
"""
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from app.config import settings
from app.utils.text_chunking import create_chunks, reassemble_cleaned_chunks, count_words

logger = logging.getLogger(__name__)


class LLMCleanupError(Exception):
    """
    Custom exception for LLM cleanup failures that preserves debug information.

    Attributes:
        message: Error message
        llm_raw_response: Raw response from LLM (if available)
        prompt_template_id: ID of prompt template used (if available)
    """

    def __init__(
        self,
        message: str,
        llm_raw_response: Optional[str] = None,
        prompt_template_id: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.llm_raw_response = llm_raw_response
        self.prompt_template_id = prompt_template_id


class LLMCleanupService(ABC):
    """Abstract base class for LLM cleanup service implementations."""

    @abstractmethod
    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using an LLM.

        Returns plain text with paragraph breaks (no JSON, no analysis).
        Use analyze_text() separately for analysis extraction.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for LLM sampling (0.0-2.0). If None, uses default.
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, uses default.
            model: Model to use for cleanup. If None, uses the service's default model.

        Returns:
            Dict containing:
                - cleaned_text: str (plain text with paragraph breaks)
                - prompt_template_id: Optional[int]
                - llm_raw_response: str (original response with <break> markers)
                - temperature: Optional[float]
                - top_p: Optional[float]

        Raises:
            LLMCleanupError: If cleanup fails after retries
        """
        pass

    @abstractmethod
    async def analyze_text(
        self,
        cleaned_text: str,
        entry_type: str = "dream",
        analysis_temperature: Optional[float] = None,
        analysis_top_p: Optional[float] = None,
        analysis_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract analysis from cleaned text (themes, emotions, etc.).

        Analysis has separate LLM parameters from cleanup, allowing different
        temperature/model settings for each step.

        Args:
            cleaned_text: Cleaned text to analyze
            entry_type: Type of entry for schema lookup
            analysis_temperature: Temperature for analysis LLM sampling (separate from cleanup)
            analysis_top_p: Top-p for analysis nucleus sampling (separate from cleanup)
            analysis_model: Model to use for analysis (separate from cleanup model)

        Returns:
            Dict containing:
                - analysis: dict with entry_type-specific fields
                - llm_raw_response: str

        Raises:
            LLMCleanupError: If analysis fails after retries
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name used by this service.

        Returns:
            Model name string (e.g., "ollama-llama3.2:3b", "groq-llama-3.3-70b-versatile")
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name for this service.

        Returns:
            Provider name string (e.g., "ollama", "groq")
        """
        pass

    @abstractmethod
    async def test_connection(self) -> bool:
        """
        Test connection to the LLM service.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Get list of available LLM models for this provider.

        Returns:
            List of dicts with model information (id, name, optional metadata)
        """
        pass

    async def cleanup_transcription_with_chunking(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None,
        enable_chunking: bool = False,
        chunk_max_words: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Clean up transcription with optional smart chunking for long texts.

        When enable_chunking=True and text exceeds threshold:
        1. Splits text into sentence-bounded chunks
        2. Processes each chunk independently
        3. Reassembles cleaned chunks

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, etc.)
            temperature: Temperature for LLM sampling
            top_p: Top-p for nucleus sampling
            model: Model to use for cleanup
            enable_chunking: Whether to enable smart chunking (default: False)
            chunk_max_words: Override default chunk size (default: settings.CHUNK_MAX_WORDS)

        Returns:
            Dict containing cleaned_text, prompt_template_id, llm_raw_response,
            temperature, top_p, and optionally chunking_metadata
        """
        max_words = chunk_max_words or settings.CHUNK_MAX_WORDS
        word_count = count_words(transcription_text)

        # Check if chunking should be applied
        should_chunk = enable_chunking and word_count > max_words

        if not should_chunk:
            # Standard processing without chunking
            result = await self.cleanup_transcription(
                transcription_text=transcription_text,
                entry_type=entry_type,
                temperature=temperature,
                top_p=top_p,
                model=model
            )

            # Add chunking metadata if chunking was requested but not used
            if enable_chunking:
                result["chunking_metadata"] = {
                    "enabled": True,
                    "used": False,
                    "reason": "text_under_threshold",
                    "word_count": word_count,
                    "threshold_words": max_words
                }

            return result

        # Apply chunking
        chunks = create_chunks(
            text=transcription_text,
            max_words=max_words
        )

        logger.info(
            f"Processing {len(chunks)} chunks for cleanup (word_count={word_count})"
        )

        cleaned_chunks = []
        raw_responses = []
        prompt_template_id = None

        for i, chunk in enumerate(chunks):
            logger.debug(f"Processing chunk {i+1}/{len(chunks)}")

            chunk_result = await self.cleanup_transcription(
                transcription_text=chunk,
                entry_type=entry_type,
                temperature=temperature,
                top_p=top_p,
                model=model
            )

            cleaned_chunks.append(chunk_result["cleaned_text"])
            raw_responses.append(
                f"--- Chunk {i+1}/{len(chunks)} ---\n{chunk_result.get('llm_raw_response', '')}"
            )

            # Capture prompt_template_id from first chunk
            if prompt_template_id is None:
                prompt_template_id = chunk_result.get("prompt_template_id")

        # Reassemble cleaned chunks
        combined_cleaned_text = reassemble_cleaned_chunks(cleaned_chunks)
        combined_raw_response = "\n\n".join(raw_responses)

        return {
            "cleaned_text": combined_cleaned_text,
            "llm_raw_response": combined_raw_response,
            "prompt_template_id": prompt_template_id,
            "temperature": temperature,
            "top_p": top_p,
            "chunking_metadata": {
                "enabled": True,
                "used": True,
                "chunk_count": len(chunks),
                "original_word_count": word_count,
                "threshold_words": max_words
            }
        }
