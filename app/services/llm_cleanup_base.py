"""
Abstract base class for LLM cleanup services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class LLMCleanupService(ABC):
    """Abstract base class for LLM cleanup service implementations."""

    @abstractmethod
    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using an LLM.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for LLM sampling (0.0-2.0). If None, uses default.
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, uses default.

        Returns:
            Dict containing:
                - cleaned_text: str
                - analysis: dict with themes, emotions, characters, locations
                - prompt_template_id: Optional[int]
                - llm_raw_response: str
                - temperature: Optional[float] - temperature used
                - top_p: Optional[float] - top_p used

        Raises:
            Exception: If cleanup fails after retries
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
