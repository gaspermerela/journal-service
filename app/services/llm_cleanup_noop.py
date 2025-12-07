"""
NoOp LLM Cleanup Service for testing.
Returns mock data without calling any actual LLM.
"""
from typing import Dict, Any, Optional

from app.services.llm_cleanup_base import LLMCleanupService
from app.utils.logger import get_logger


logger = get_logger("services.llm_cleanup_noop")


class NoOpLLMCleanupService(LLMCleanupService):
    """No-operation LLM cleanup service for testing."""

    def __init__(self, model_name: str = "noop-test-model"):
        self.model_name = model_name
        logger.info(f"NoOpLLMCleanupService initialized with model={model_name}")

    def get_model_name(self) -> str:
        """Return the configured model name."""
        return self.model_name

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "noop"

    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return mock cleaned data without calling any LLM.

        Args:
            transcription_text: Raw transcription text
            entry_type: Type of entry (dream, journal, etc.)
            temperature: Temperature parameter (unused in NoOp)
            top_p: Top-p parameter (unused in NoOp)
            model: Model to use (unused in NoOp)

        Returns:
            Dict with mock cleaned data (plain text, no analysis)
        """
        logger.info(
            f"NoOp cleanup called for entry_type={entry_type}, "
            f"text_length={len(transcription_text)}, "
            f"temperature={temperature}, top_p={top_p}, model={model}"
        )

        return {
            "cleaned_text": f"[NoOp Cleaned] {transcription_text}",
            "prompt_template_id": None,
            "llm_raw_response": f"[NoOp Cleaned] {transcription_text}",
            "temperature": temperature,
            "top_p": top_p
        }

    async def analyze_text(
        self,
        cleaned_text: str,
        entry_type: str = "dream",
        analysis_temperature: Optional[float] = None,
        analysis_top_p: Optional[float] = None,
        analysis_model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Return mock analysis data without calling any LLM.

        Args:
            cleaned_text: Cleaned text to analyze
            entry_type: Type of entry (dream, journal, etc.)
            analysis_temperature: Temperature parameter (unused in NoOp)
            analysis_top_p: Top-p parameter (unused in NoOp)
            analysis_model: Model to use (unused in NoOp)

        Returns:
            Dict with mock analysis data
        """
        logger.info(
            f"NoOp analyze called for entry_type={entry_type}, "
            f"text_length={len(cleaned_text)}, "
            f"analysis_temperature={analysis_temperature}, analysis_top_p={analysis_top_p}, "
            f"analysis_model={analysis_model}"
        )

        return {
            "analysis": {
                "themes": ["test", "mock"],
                "emotions": ["neutral"],
                "characters": [],
                "locations": []
            },
            "llm_raw_response": '{"themes": ["test", "mock"], "emotions": ["neutral"], "characters": [], "locations": []}'
        }

    async def test_connection(self) -> bool:
        """
        Test connection (always succeeds for NoOp).

        Returns:
            Always True
        """
        return True

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """Return mock list of available models for testing."""
        return [
            {"id": "noop-llm-test", "name": "NoOp Test Model"}
        ]
