"""
Groq LLM Cleanup Service implementation.
"""
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from groq import AsyncGroq
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings, get_output_schema, generate_json_schema_instruction
from app.models.prompt_template import PromptTemplate
from app.services.llm_cleanup_base import LLMCleanupService, LLMCleanupError
from app.services.llm_cleanup_ollama import (
    DREAM_CLEANUP_PROMPT,
    GENERIC_CLEANUP_PROMPT,
    DREAM_ANALYSIS_PROMPT,
    GENERIC_ANALYSIS_PROMPT,
)
from app.utils.logger import get_logger

logger = get_logger("services.llm_cleanup_groq")

INVALID_CHARS = (
        r"[\x00-\x09\x0B-\x1F\x7F"  # ASCII control characters EXCEPT newline (\x0A)
        r"\u2028\u2029"  # Unicode line/paragraph separators
        r"\u200B\u200C\u200D"  # zero-width spaces
        r"\u00AD"  # soft hyphen
        r"]"
    )

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

        # Cache for list_available_models() with 1-hour TTL
        self._models_cache: Optional[list[Dict[str, Any]]] = None
        self._models_cache_timestamp: Optional[datetime] = None
        self._cache_ttl = timedelta(hours=1)

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

    def _get_hardcoded_analysis_prompt(self, entry_type: str) -> str:
        """
        Get hardcoded analysis prompt (JSON output).
        """
        if entry_type == "dream":
            return DREAM_ANALYSIS_PROMPT
        else:
            return GENERIC_ANALYSIS_PROMPT

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

    def _get_analysis_prompt(self, entry_type: str) -> str:
        """
        Get analysis prompt template with JSON schema instruction inserted.

        Only replaces {output_format} if present - does NOT append if missing.

        Returns:
            Complete prompt with JSON schema instruction (if placeholder exists)
        """
        prompt_text = self._get_hardcoded_analysis_prompt(entry_type)

        # Only replace {output_format} if present in the prompt
        if "{output_format}" in prompt_text:
            # Generate JSON schema instruction based on entry_type
            try:
                schema_instruction = generate_json_schema_instruction(entry_type)
            except ValueError:
                logger.error(
                    f"Unknown entry_type for schema generation, using 'dream' fallback",
                    entry_type=entry_type
                )
                schema_instruction = generate_json_schema_instruction("dream")

            return prompt_text.replace("{output_format}", schema_instruction)
        else:
            # No placeholder - return prompt as-is (don't append schema)
            return prompt_text

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

        Returns plain text with paragraph breaks (no JSON, no analysis).
        Use analyze_text() separately for analysis extraction.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for LLM sampling (0.0-2.0). If None, uses default.
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, Groq uses default.
            model: Model to use for cleanup. If None, uses the service's default model.

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
        # Use provided model or fall back to instance default
        effective_model = model if model else self.model

        prompt_template, template_id = await self._get_cleanup_prompt(entry_type)
        prompt = prompt_template.format(transcription_text=transcription_text)

        last_raw_response = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM cleanup attempt {attempt + 1}/{self.max_retries + 1} "
                    f"using Groq model {effective_model}, temperature={temperature}, top_p={top_p}"
                )
                result = await self._call_groq_cleanup(
                    prompt,
                    temperature=temperature,
                    top_p=top_p,
                    model=effective_model
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

        Args:
            cleaned_text: Cleaned text to analyze
            entry_type: Type of entry for schema lookup
            analysis_temperature: Temperature for analysis LLM sampling (separate from cleanup)
            analysis_top_p: Top-p for analysis nucleus sampling (separate from cleanup)
            analysis_model: Model to use for analysis

        Returns:
            Dict containing:
            - analysis: dict with entry_type-specific fields
            - llm_raw_response: str

        Raises:
            LLMCleanupError: If analysis fails after retries
        """
        effective_model = analysis_model if analysis_model else self.model

        prompt_template = self._get_analysis_prompt(entry_type)
        prompt = prompt_template.format(cleaned_text=cleaned_text)

        last_raw_response = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM analysis attempt {attempt + 1}/{self.max_retries + 1} "
                    f"using Groq model {effective_model}, temperature={analysis_temperature}, top_p={analysis_top_p}"
                )
                result = await self._call_groq_analysis(
                    prompt,
                    entry_type=entry_type,
                    temperature=analysis_temperature,
                    top_p=analysis_top_p,
                    model=effective_model
                )
                return result
            except Exception as e:
                if hasattr(e, 'llm_raw_response'):
                    last_raw_response = e.llm_raw_response

                logger.warning(
                    f"LLM analysis attempt {attempt + 1} failed: {str(e)}"
                )
                if attempt == self.max_retries:
                    logger.error("All LLM analysis attempts failed")
                    raise LLMCleanupError(
                        message=str(e),
                        llm_raw_response=last_raw_response,
                        prompt_template_id=None
                    ) from e

        raise LLMCleanupError(
            message="LLM analysis failed unexpectedly",
            llm_raw_response=last_raw_response,
            prompt_template_id=None
        )

    async def _call_groq_cleanup(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Groq API for cleanup (plain text response with <break> markers).

        Args:
            prompt: Formatted prompt to send to LLM
            temperature: Temperature for sampling. If None, uses default.
            top_p: Top-p for nucleus sampling. If None, Groq uses default.
            model: Model to use. If None, uses self.model.

        Returns:
            Dict containing cleaned_text and llm_raw_response

        Raises:
            Exception: If API call fails
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
                "temperature": temperature,
                "max_tokens": 5000,
                "timeout": self.timeout
            }

            # Add top_p if provided
            if top_p is not None:
                api_params["top_p"] = top_p

            # Call Groq chat completion API
            response = await self.client.chat.completions.create(**api_params)

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"Raw cleanup Groq response: {response_text[:200]}...")

            # Process plain text response: convert <break> to paragraph breaks
            cleaned_text = self._process_cleanup_response(response_text)

            return {
                "cleaned_text": cleaned_text,
                "llm_raw_response": response_text
            }

        except Exception as e:
            logger.error(f"Groq cleanup API call failed: {str(e)}", exc_info=True)
            raise

    async def _call_groq_analysis(
        self,
        prompt: str,
        entry_type: str = "dream",
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        model: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call Groq API for analysis (JSON response).

        Args:
            prompt: Formatted prompt to send to LLM
            entry_type: Entry type for schema-based parsing
            temperature: Temperature for sampling. If None, uses default.
            top_p: Top-p for nucleus sampling. If None, Groq uses default.
            model: Model to use. If None, uses self.model.

        Returns:
            Dict containing analysis and llm_raw_response

        Raises:
            Exception: If API call fails
            ValueError: If response is not valid JSON
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
                "temperature": temperature,
                "max_tokens": 5000,
                "timeout": self.timeout
            }

            # Add top_p if provided
            if top_p is not None:
                api_params["top_p"] = top_p

            # Call Groq chat completion API
            response = await self.client.chat.completions.create(**api_params)

            # Extract response text
            response_text = response.choices[0].message.content

            logger.debug(f"Raw analysis Groq response: {response_text[:200]}...")

            # Parse the JSON response with schema-based parsing
            try:
                result = self._parse_analysis_response(response_text, entry_type)
            except (ValueError, json.JSONDecodeError) as parse_error:
                # Attach raw response to parsing exceptions for debugging
                parse_error.llm_raw_response = response_text
                raise

            # Include raw response for debugging and storage
            result["llm_raw_response"] = response_text

            return result

        except Exception as e:
            logger.error(f"Groq analysis API call failed: {str(e)}", exc_info=True)
            raise

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

    def sanitize_for_json(self, text: str) -> str:
        """Remove invalid JSON characters from text."""
        return re.sub(INVALID_CHARS, "", text)

    def _parse_analysis_response(self, response_text: str, entry_type: str = "dream") -> Dict[str, Any]:
        """
        Parse and validate LLM JSON response for analysis using OUTPUT_SCHEMAS.

        Args:
            response_text: Raw response from LLM (should be JSON)
            entry_type: Entry type for schema lookup

        Returns:
            Dict containing analysis fields

        Raises:
            ValueError: If response is not valid JSON
        """
        logger.debug(
            "Parsing analysis response",
            entry_type=entry_type,
            response_length=len(response_text)
        )

        # Strip markdown code blocks if present
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:]  # Remove ```json
        elif text.startswith("```"):
            text = text[3:]  # Remove ```
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        # Parse JSON
        try:
            text = self.sanitize_for_json(text)
            parsed = json.loads(text)
        except json.JSONDecodeError as e:
            logger.error("Failed to parse analysis response as JSON", error=str(e))
            raise ValueError(f"Analysis response is not valid JSON: {e}")

        # Get schema for this entry_type
        try:
            schema = get_output_schema(entry_type)
        except ValueError:
            logger.warning(
                "Unknown entry_type, using 'dream' schema fallback",
                entry_type=entry_type
            )
            schema = get_output_schema("dream")

        # Parse analysis fields with graceful degradation
        analysis = {}
        for field_name in schema["fields"].keys():
            # Use .get() with default - tolerates missing fields
            analysis[field_name] = parsed.get(field_name, [])

        return {"analysis": analysis}

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

        Uses 1-hour cache to reduce API calls.

        Returns:
            List of dicts with LLM model information

        Raises:
            RuntimeError: If API request fails
        """
        # Check cache first
        if self._models_cache is not None and self._models_cache_timestamp is not None:
            if datetime.now() - self._models_cache_timestamp < self._cache_ttl:
                logger.debug(f"Returning cached Groq LLM models ({len(self._models_cache)} models)")
                return self._models_cache

        # Cache miss or expired - fetch from API
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

            # Sort by context window (descending) then by name (alphabetical)
            # This puts most capable models first, with consistent ordering
            llm_models.sort(key=lambda m: (-m.get("context_window", 0), m["id"]))

            # Update cache
            self._models_cache = llm_models
            self._models_cache_timestamp = datetime.now()

            logger.info(f"Fetched and cached {len(llm_models)} Groq LLM models (cache TTL: 1 hour)")
            return llm_models

        except Exception as e:
            logger.error(f"Failed to fetch Groq models: {e}", exc_info=True)
            raise RuntimeError(f"Failed to fetch Groq models: {str(e)}") from e
