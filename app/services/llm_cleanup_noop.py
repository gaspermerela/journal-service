"""
NoOp LLM Cleanup Service for testing.
Returns mock data without calling any actual LLM.
"""
from typing import Dict, Any

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
        entry_type: str = "dream"
    ) -> Dict[str, Any]:
        """
        Return mock cleaned data without calling any LLM.

        Args:
            transcription_text: Raw transcription text
            entry_type: Type of entry (dream, journal, etc.)

        Returns:
            Dict with mock cleaned data
        """
        logger.info(f"NoOp cleanup called for entry_type={entry_type}, text_length={len(transcription_text)}")

        return {
            "cleaned_text": f"[NoOp Cleaned] {transcription_text}",
            "analysis": {
                "themes": ["test", "mock"],
                "emotions": ["neutral"],
                "characters": [],
                "locations": []
            },
            "prompt_template_id": None,
            "llm_raw_response": '{"cleaned_text": "[NoOp Cleaned] ' + transcription_text + '"}'
        }

    async def test_connection(self) -> bool:
        """
        Test connection (always succeeds for NoOp).

        Returns:
            Always True
        """
        return True
