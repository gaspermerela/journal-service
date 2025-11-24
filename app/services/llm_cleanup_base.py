"""
Abstract base class for LLM cleanup services.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class LLMCleanupService(ABC):
    """Abstract base class for LLM cleanup service implementations."""

    @abstractmethod
    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream"
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using an LLM.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)

        Returns:
            Dict containing:
                - cleaned_text: str
                - analysis: dict with themes, emotions, characters, locations
                - prompt_template_id: Optional[int]
                - llm_raw_response: str

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
