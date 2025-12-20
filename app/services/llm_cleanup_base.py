"""
Abstract base class for LLM cleanup services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


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
