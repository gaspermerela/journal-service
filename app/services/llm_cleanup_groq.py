"""
Groq LLM Cleanup Service implementation.
"""
import json
from typing import Dict, Any, Optional, Tuple

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import settings
from app.models.prompt_template import PromptTemplate
from app.utils.logger import get_logger
from app.services.llm_cleanup_base import LLMCleanupService
from app.services.llm_cleanup_ollama import DREAM_CLEANUP_PROMPT, GENERIC_CLEANUP_PROMPT


logger = get_logger("services.llm_cleanup_groq")


class GroqLLMCleanupService(LLMCleanupService):
    """Service for cleaning transcriptions using Groq's chat completion API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        db_session: Optional[AsyncSession] = None
    ):
        """
        Initialize Groq LLM cleanup service.

        Args:
            api_key: Groq API key (if None, uses settings.GROQ_API_KEY)
            model: Groq model name (if None, uses settings.GROQ_LLM_MODEL)
            db_session: Optional database session for prompt template lookup
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_LLM_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES
        self.db_session = db_session
        self.client = AsyncGroq(api_key=self.api_key)

        if not self.api_key:
            raise ValueError("GROQ_API_KEY is required for GroqLLMCleanupService")

        logger.info(f"GroqLLMCleanupService initialized with model={self.model}")

    def get_model_name(self) -> str:
        """Return model name in format: groq-{model}"""
        return f"groq-{self.model}"

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "groq"

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

    def _get_hardcoded_fallback_prompt(self, entry_type: str) -> str:
        """
        Get hardcoded fallback prompt when database lookup fails.

        This ensures the service always works even if:
        - Database is unavailable
        - No active prompt is set
        - Prompt template is invalid
        """
        if entry_type == "dream":
            return DREAM_CLEANUP_PROMPT
        else:
            return GENERIC_CLEANUP_PROMPT

    async def _get_prompt_template(self, entry_type: str) -> Tuple[str, Optional[int]]:
        """
        Get prompt template with robust fallback chain.

        Fallback order:
        1. Try to load active prompt from database
        2. Fall back to hardcoded constants if DB fails

        Returns:
            Tuple of (prompt_text, template_id or None)
        """
        # Try database first
        db_result = await self._get_prompt_from_db(entry_type)
        if db_result:
            return db_result

        # Fallback to hardcoded prompts
        logger.warning(
            f"Using hardcoded fallback prompt for entry_type '{entry_type}' "
            f"(database lookup failed or no active template)"
        )
        fallback_prompt = self._get_hardcoded_fallback_prompt(entry_type)
        return (fallback_prompt, None)

    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using Groq's chat completion API.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for LLM sampling (0.0-2.0). If None, uses default (0.3).
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, Groq uses default.
            model: Model to use for cleanup. If None, uses the service's default model.

        Returns:
            Dict containing cleaned_text, analysis, prompt_template_id, temperature, and top_p

        Raises:
            Exception: If cleanup fails after retries
        """
        # Use provided model or fall back to instance default
        effective_model = model if model else self.model

        prompt_template, template_id = await self._get_prompt_template(entry_type)
        prompt = prompt_template.format(transcription_text=transcription_text)

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM cleanup attempt {attempt + 1}/{self.max_retries + 1} "
                    f"using Groq model {effective_model}, temperature={temperature}, top_p={top_p}"
                )
                result = await self._call_groq(prompt, temperature=temperature, top_p=top_p, model=effective_model)

                # Add prompt_template_id and parameters to result
                result["prompt_template_id"] = template_id
                result["temperature"] = temperature if temperature is not None else 0.3
                result["top_p"] = top_p

                return result
            except Exception as e:
                logger.warning(
                    f"LLM cleanup attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt == self.max_retries:
                    logger.error("All LLM cleanup attempts failed")
                    raise

        # Should never reach here
        raise Exception("LLM cleanup failed unexpectedly")

    async def _call_groq(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Groq chat completion API to process the prompt.

        Args:
            prompt: Formatted prompt to send to LLM
            temperature: Temperature for sampling (0.0-2.0). If None, uses default (0.3).
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, Groq uses default.
            model: Model to use. If None, uses self.model.

        Returns:
            Dict containing cleaned_text and analysis

        Raises:
            Exception: If API call fails
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If response missing required fields
        """
        effective_model = model if model else self.model

        try:
            # Build API call parameters
            api_params = {
                "model": effective_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature if temperature is not None else 0.3,
                "max_tokens": 2000,
                "timeout": self.timeout
            }

            # Add top_p if provided
            if top_p is not None:
                api_params["top_p"] = top_p

            # Call Groq chat completion API
            response = await self.client.chat.completions.create(**api_params)

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"Raw Groq LLM response: {response_text[:200]}...")

            # Parse the JSON response
            result = self._parse_llm_response(response_text)

            # Include raw response for debugging and storage
            result["llm_raw_response"] = response_text

            return result

        except Exception as e:
            logger.error(f"Groq API call failed: {str(e)}", exc_info=True)
            raise

    def _parse_llm_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse LLM response and extract structured data.

        Args:
            response_text: Raw response from LLM

        Returns:
            Dict containing cleaned_text and analysis

        Raises:
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If response missing required fields
        """
        # Remove markdown code blocks if present
        cleaned_response = response_text.strip()
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
        if cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
        if cleaned_response.endswith("```"):
            cleaned_response = cleaned_response[:-3]

        cleaned_response = cleaned_response.strip()

        # Parse JSON
        try:
            parsed = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {cleaned_response[:200]}")
            raise ValueError(f"LLM returned invalid JSON: {str(e)}")

        # Validate required fields
        if "cleaned_text" not in parsed:
            raise KeyError("LLM response missing 'cleaned_text' field")

        # Ensure analysis fields exist with defaults
        result = {
            "cleaned_text": parsed["cleaned_text"],
            "analysis": {
                "themes": parsed.get("themes", []),
                "emotions": parsed.get("emotions", []),
                "characters": parsed.get("characters", []),
                "locations": parsed.get("locations", [])
            }
        }

        return result

    async def test_connection(self) -> bool:
        """
        Test connection to Groq service.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Try to list models as a connection test
            await self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Groq connection test failed: {str(e)}")
            return False

    async def list_available_models(self) -> list[Dict[str, Any]]:
        """
        Fetch available LLM models from Groq API.
        Filters out whisper models (those are for transcription).

        Returns:
            List of dicts with LLM model information

        Raises:
            RuntimeError: If API request fails
        """
        try:
            import httpx

            url = "https://api.groq.com/openai/v1/models"
            headers = {"Authorization": f"Bearer {self.api_key}"}

            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

            # Exclude whisper models (transcription only), keep LLM models
            llm_models = [
                {
                    "id": model["id"],
                    "name": model["id"],
                    "owned_by": model.get("owned_by"),
                    "context_window": model.get("context_window"),
                    "active": model.get("active", True)
                }
                for model in data.get("data", [])
                if not (model["id"].startswith("whisper-") or model["id"].startswith("distil-whisper-"))
            ]

            logger.info(f"Found {len(llm_models)} Groq LLM models")
            return llm_models

        except Exception as e:
            logger.error(f"Failed to fetch Groq models: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch Groq models: {str(e)}") from e
