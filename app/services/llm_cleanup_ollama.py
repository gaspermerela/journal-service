"""
Ollama LLM Cleanup Service implementation.
"""
import re
from typing import Dict, Any, Optional, Tuple

import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.prompt_template import PromptTemplate
from app.utils.logger import get_logger
from app.services.llm_cleanup_base import LLMCleanupService, LLMCleanupError


logger = get_logger("services.llm_cleanup_ollama")


# Cleanup prompt templates - output plain text with <break> markers for paragraphs
DREAM_CLEANUP_PROMPT = """You are a dream journal assistant. Clean up this voice transcription of a dream.

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Keep the original meaning and emotional tone intact
4. Use <break> to separate paragraphs (NOT newlines)

Output ONLY the cleaned text with <break> markers between paragraphs.
No JSON, no explanations, no analysis - just the cleaned text."""


GENERIC_CLEANUP_PROMPT = """You are a transcription cleanup assistant. Clean up this voice transcription.

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Keep the original meaning and tone intact
4. Use <break> to separate paragraphs (NOT newlines)

Output ONLY the cleaned text with <break> markers between paragraphs.
No JSON, no explanations, no analysis - just the cleaned text."""


class OllamaLLMCleanupService(LLMCleanupService):
    """Service for cleaning transcriptions using local LLM (Ollama)."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES
        self.db_session = db_session

    def get_model_name(self) -> str:
        """Return model name in format: ollama-{model}"""
        return f"ollama-{self.model}"

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "ollama"

    async def _get_prompt_from_db(self, entry_type: str) -> Optional[Tuple[str, int]]:
        """
        Get active prompt template from database.

        Returns:
            Tuple of (prompt_text, template_id) if found, None otherwise
        """
        if not self.db_session:
            logger.warning("No database session provided, skipping DB prompt lookup")
            return None

        try:
            stmt = (
                select(PromptTemplate)
                .where(
                    PromptTemplate.entry_type == entry_type,
                    PromptTemplate.is_active == True
                )
                .order_by(PromptTemplate.updated_at.desc())
            )
            result = await self.db_session.execute(stmt)
            template = result.scalars().first()

            if template:
                # Validate prompt template
                if not template.is_valid:
                    logger.error(
                        f"Active prompt template {template.id} for entry_type '{entry_type}' "
                        f"is invalid (missing prompt_text or {{transcription_text}} placeholder)"
                    )
                    return None

                logger.info(
                    f"Using prompt template '{template.name}' (id={template.id}, v{template.version}) "
                    f"for entry_type '{entry_type}'"
                )
                return (template.prompt_text, template.id)
            else:
                logger.warning(f"No active prompt template found for entry_type '{entry_type}'")
                return None

        except Exception as e:
            logger.error(f"Error fetching prompt from database: {str(e)}")
            return None

    def _get_hardcoded_cleanup_prompt(self, entry_type: str) -> str:
        """
        Get hardcoded cleanup prompt (plain text output with <break> markers).

        This ensures the service always works even if:
        - Database is unavailable
        - No active prompt is set
        - Prompt template is invalid
        """
        if entry_type == "dream":
            return DREAM_CLEANUP_PROMPT
        else:
            return GENERIC_CLEANUP_PROMPT

    async def _get_cleanup_prompt(self, entry_type: str) -> Tuple[str, Optional[int]]:
        """
        Get cleanup prompt template (plain text output, no JSON schema).

        Tries database first, falls back to hardcoded prompts.
        Cleanup prompts don't use {output_format} - it's simply replaced with empty string.

        Returns:
            Tuple of (prompt_text, template_id or None)
        """
        # Try database first
        db_result = await self._get_prompt_from_db(entry_type)
        if db_result:
            prompt_text, template_id = db_result
            # Cleanup prompts don't use {output_format} - just remove it
            prompt_text = prompt_text.replace("{output_format}", "")
        else:
            # Fallback to hardcoded cleanup prompts
            logger.warning(
                f"Using hardcoded fallback cleanup prompt for entry_type '{entry_type}' "
                f"(database lookup failed or no active template)"
            )
            prompt_text = self._get_hardcoded_cleanup_prompt(entry_type)
            template_id = None

        return (prompt_text, template_id)

    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using Ollama LLM.

        Returns plain text with paragraph breaks (no JSON, no analysis).

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for LLM sampling (0.0-2.0). If None, uses default (0.3).
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, uses default.
            model: Model to use for cleanup. IGNORED for local Ollama (uses configured model).

        Returns:
            Dict containing:
            - cleaned_text: str (plain text with paragraph breaks)
            - prompt_template_id: Optional[int]
            - temperature: Optional[float]
            - top_p: Optional[float]
            - llm_raw_response: str (original response with <break> markers)

        Raises:
            LLMCleanupError: If cleanup fails after retries (includes debug info)
        """
        # Log warning if model selection requested but not supported
        if model and model != self.model:
            logger.warning(
                f"Model selection not supported for local Ollama. "
                f"Requested: {model}, Using: {self.model}"
            )

        prompt_template, template_id = await self._get_cleanup_prompt(entry_type)
        prompt = prompt_template.format(transcription_text=transcription_text)

        last_raw_response = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM cleanup attempt {attempt + 1}/{self.max_retries + 1} "
                    f"using model {self.model}, temperature={temperature}, top_p={top_p}"
                )
                result = await self._call_ollama_cleanup(
                    prompt,
                    temperature=temperature,
                    top_p=top_p
                )

                # Add prompt_template_id and parameters to result
                result["prompt_template_id"] = template_id
                result["temperature"] = temperature
                result["top_p"] = top_p

                return result
            except Exception as e:
                # Try to extract raw response if it's in the exception context
                if hasattr(e, 'llm_raw_response'):
                    last_raw_response = e.llm_raw_response

                logger.warning(
                    f"LLM cleanup attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt == self.max_retries:
                    logger.error("All LLM cleanup attempts failed")
                    # Raise custom exception with debug info
                    raise LLMCleanupError(
                        message=str(e),
                        llm_raw_response=last_raw_response,
                        prompt_template_id=template_id
                    ) from e

        # Should never reach here
        raise LLMCleanupError(
            message="LLM cleanup failed unexpectedly",
            llm_raw_response=last_raw_response,
            prompt_template_id=template_id
        )

    async def _call_ollama_cleanup(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Call Ollama API for cleanup (plain text response with <break> markers).

        Args:
            prompt: Formatted prompt to send to LLM
            temperature: Temperature for sampling (0.0-2.0). If None, uses default (0.3).
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, Ollama uses default.

        Returns:
            Dict containing cleaned_text and llm_raw_response

        Raises:
            httpx.HTTPError: If API call fails
        """
        url = f"{self.base_url}/api/generate"

        # Build options dict with provided parameters
        options = {}
        if temperature is not None:
            options["temperature"] = temperature
        else:
            options["temperature"] = 0.3  # Default for consistent output

        if top_p is not None:
            options["top_p"] = top_p

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": options
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            response_text = data.get("response", "")

            logger.debug(f"Raw cleanup LLM response: {response_text[:200]}...")

            # Process plain text response: convert <break> to paragraph breaks
            cleaned_text = self._process_cleanup_response(response_text)

            return {
                "cleaned_text": cleaned_text,
                "llm_raw_response": response_text
            }

    def _process_cleanup_response(self, response_text: str) -> str:
        """
        Process cleanup response: convert <break> markers to paragraph breaks.

        Args:
            response_text: Raw LLM response with <break> markers

        Returns:
            Cleaned text with double newlines for paragraphs
        """
        text = response_text.strip()
        # Convert <break> markers to double newlines
        text = text.replace("<break>", "\n\n")
        # Clean up any excessive whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text

    async def test_connection(self) -> bool:
        """
        Test connection to Ollama service.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self.base_url}/api/tags"
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Ollama connection test failed: {str(e)}")
            return False

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Return hardcoded list of common Ollama models.

        Returns:
            List of dicts with model information
        """
        return [
            {"id": "llama3.2:3b", "name": "Llama 3.2 3B"},
            {"id": "llama3.2:1b", "name": "Llama 3.2 1B"},
            {"id": "llama3.1:8b", "name": "Llama 3.1 8B"},
            {"id": "llama3.1:70b", "name": "Llama 3.1 70B"},
            {"id": "qwen2.5:7b", "name": "Qwen 2.5 7B"},
            {"id": "mistral:7b", "name": "Mistral 7B"}
        ]
