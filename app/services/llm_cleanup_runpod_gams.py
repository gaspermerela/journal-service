"""
GaMS (Generative Model for Slovene) LLM Cleanup Service on RunPod.

This service calls a RunPod serverless endpoint running the GaMS-9B-Instruct model
for native Slovenian text cleanup. The model is optimized for Slovenian language.

"""
import asyncio
import re
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.prompt_template import PromptTemplate
from app.services.llm_cleanup_base import (
    LLMCleanupError,
    LLMCleanupService,
    DREAM_CLEANUP_PROMPT,
    GENERIC_CLEANUP_PROMPT,
)
from app.utils.logger import get_logger

logger = get_logger("services.llm_cleanup_runpod_gams")

# RunPod API base URL
RUNPOD_API_BASE = "https://api.runpod.ai/v2"


class RunPodGamsLLMCleanupService(LLMCleanupService):
    """Service for cleaning transcriptions using GaMS LLM on RunPod serverless."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_id: Optional[str] = None,
        model: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ):
        """
        Initialize GaMS LLM cleanup service on RunPod.

        Args:
            api_key: RunPod API key (if None, uses settings.RUNPOD_API_KEY)
            endpoint_id: RunPod endpoint ID (if None, uses settings.RUNPOD_LLM_GAMS_ENDPOINT_ID)
            model: GaMS model variant (if None, uses settings.RUNPOD_LLM_GAMS_MODEL)
            db_session: Optional database session for prompt template lookup
        """
        self.api_key = api_key or settings.RUNPOD_API_KEY
        self.endpoint_id = endpoint_id or settings.RUNPOD_LLM_GAMS_ENDPOINT_ID
        self.model = model or settings.RUNPOD_LLM_GAMS_MODEL
        self.timeout = settings.RUNPOD_LLM_GAMS_TIMEOUT
        self.max_retries = settings.RUNPOD_LLM_GAMS_MAX_RETRIES
        self.default_temperature = settings.RUNPOD_LLM_GAMS_DEFAULT_TEMPERATURE
        self.default_top_p = settings.RUNPOD_LLM_GAMS_DEFAULT_TOP_P
        self.max_tokens = settings.RUNPOD_LLM_GAMS_MAX_TOKENS
        self.db_session = db_session

        # Cache for available models (static for GaMS)
        self._models_cache: Optional[List[Dict[str, Any]]] = None

        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY is required for RunPodGamsLLMCleanupService")
        if not self.endpoint_id:
            raise ValueError(
                "RUNPOD_LLM_GAMS_ENDPOINT_ID is required for RunPodGamsLLMCleanupService"
            )

        logger.info(
            f"RunPodGamsLLMCleanupService initialized",
            model=self.model,
            endpoint_id=self.endpoint_id[:8] + "...",
        )

    def get_model_name(self) -> str:
        """Return model name in format: runpod_llm_gams-{model}"""
        return f"runpod_llm_gams-{self.model}"

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "runpod_llm_gams"

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
                    PromptTemplate.is_active == True,
                )
                .order_by(PromptTemplate.updated_at.desc())
            )
            result = await self.db_session.execute(stmt)
            template = result.scalars().first()

            if template:
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
                logger.warning(
                    f"No active prompt template found for entry_type '{entry_type}'"
                )
                return None

        except Exception as e:
            logger.error(f"Error fetching prompt from database: {str(e)}")
            return None

    def _get_hardcoded_cleanup_prompt(self, entry_type: str) -> str:
        """
        Get hardcoded cleanup prompt (plain text output with <break> markers).

        Fallback when database is unavailable or no active prompt exists.
        """
        if entry_type == "dream":
            return DREAM_CLEANUP_PROMPT
        else:
            return GENERIC_CLEANUP_PROMPT

    async def _get_cleanup_prompt(self, entry_type: str) -> Tuple[str, Optional[int]]:
        """
        Get cleanup prompt template.

        Tries database first, falls back to hardcoded prompts.

        Returns:
            Tuple of (prompt_text, template_id or None)
        """
        db_result = await self._get_prompt_from_db(entry_type)
        if db_result:
            prompt_text, template_id = db_result
            prompt_text = prompt_text.replace("{output_format}", "")
        else:
            logger.warning(
                f"Using hardcoded fallback cleanup prompt for entry_type '{entry_type}'"
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
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using GaMS on RunPod.

        Returns plain text with paragraph breaks (no JSON, no analysis).

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)
            temperature: Temperature for sampling (0.0-2.0). If None, uses default (0.3).
            top_p: Top-p for nucleus sampling (0.0-1.0). If None, uses default (0.9).
            model: Model variant to use. If None, uses the service's default.

        Returns:
            Dict containing:
            - cleaned_text: str (plain text with paragraph breaks)
            - prompt_template_id: Optional[int]
            - temperature: Optional[float]
            - top_p: Optional[float]
            - llm_raw_response: str (original response)

        Raises:
            LLMCleanupError: If cleanup fails after retries
        """
        effective_temperature = (
            temperature if temperature is not None else self.default_temperature
        )
        effective_top_p = top_p if top_p is not None else self.default_top_p

        prompt_template, template_id = await self._get_cleanup_prompt(entry_type)
        prompt = prompt_template.format(transcription_text=transcription_text)

        last_raw_response = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"GaMS cleanup attempt {attempt + 1}/{self.max_retries + 1}",
                    model=self.model,
                    temperature=effective_temperature,
                    top_p=effective_top_p,
                )

                result = await self._call_runpod_cleanup(
                    prompt=prompt,
                    temperature=effective_temperature,
                    top_p=effective_top_p,
                )

                result["prompt_template_id"] = template_id
                result["temperature"] = temperature
                result["top_p"] = top_p

                return result

            except Exception as e:
                if hasattr(e, "llm_raw_response"):
                    last_raw_response = e.llm_raw_response

                logger.warning(
                    f"GaMS cleanup attempt {attempt + 1} failed: {str(e)}"
                )

                if attempt == self.max_retries:
                    logger.error("All GaMS cleanup attempts failed")
                    raise LLMCleanupError(
                        message=str(e),
                        llm_raw_response=last_raw_response,
                        prompt_template_id=template_id,
                    ) from e

                # Exponential backoff before retry
                await asyncio.sleep(2 ** attempt)

        raise LLMCleanupError(
            message="GaMS cleanup failed unexpectedly",
            llm_raw_response=last_raw_response,
            prompt_template_id=template_id,
        )

    async def _call_runpod_cleanup(
        self,
        prompt: str,
        temperature: float,
        top_p: float,
    ) -> Dict[str, Any]:
        """
        Call RunPod endpoint for GaMS cleanup.

        Uses the /runsync endpoint for synchronous execution.

        Args:
            prompt: Formatted prompt to send
            temperature: Sampling temperature
            top_p: Nucleus sampling parameter

        Returns:
            Dict containing cleaned_text and llm_raw_response

        Raises:
            Exception: If API call fails
        """
        url = f"{RUNPOD_API_BASE}/{self.endpoint_id}/runsync"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "input": {
                "prompt": prompt,
                "temperature": temperature,
                "top_p": top_p,
                "max_tokens": self.max_tokens,
            }
        }

        start_time = time.time()

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)

                # Handle rate limiting
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    logger.warning(
                        f"RunPod rate limited, retrying after {retry_after}s"
                    )
                    await asyncio.sleep(retry_after)
                    raise Exception(f"Rate limited, retry after {retry_after}s")

                response.raise_for_status()
                data = response.json()

            elapsed = time.time() - start_time
            logger.debug(f"RunPod API call took {elapsed:.2f}s")

            # Check for RunPod-level errors
            if data.get("status") == "FAILED":
                error_msg = data.get("error", "Unknown RunPod error")
                raise Exception(f"RunPod job failed: {error_msg}")

            # Extract output
            output = data.get("output", {})

            if "error" in output:
                raise Exception(f"GaMS handler error: {output['error']}")

            response_text = output.get("text", "")

            if not response_text:
                raise Exception("Empty response from GaMS handler")

            # Process response: convert <break> markers to paragraph breaks
            cleaned_text = self._process_cleanup_response(response_text)

            logger.info(
                f"GaMS cleanup successful",
                processing_time=output.get("processing_time"),
                prompt_tokens=output.get("token_count", {}).get("prompt"),
                completion_tokens=output.get("token_count", {}).get("completion"),
            )

            return {
                "cleaned_text": cleaned_text,
                "llm_raw_response": response_text,
            }

        except httpx.TimeoutException:
            logger.error(f"RunPod request timed out after {self.timeout}s")
            raise Exception(f"Request timed out after {self.timeout}s")
        except httpx.HTTPStatusError as e:
            logger.error(f"RunPod HTTP error: {e.response.status_code}")
            raise Exception(f"HTTP error: {e.response.status_code}")
        except Exception as e:
            logger.error(f"RunPod API call failed: {str(e)}", exc_info=True)
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
        text = text.replace("<break>", "\n\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    async def test_connection(self) -> bool:
        """
        Test connection to RunPod endpoint.

        Sends a minimal health check request.

        Returns:
            True if connection successful, False otherwise
        """
        url = f"{RUNPOD_API_BASE}/{self.endpoint_id}/health"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()

                # Check if workers are available
                workers = data.get("workers", {})
                ready = workers.get("ready", 0)
                running = workers.get("running", 0)

                logger.info(
                    f"RunPod endpoint health check",
                    ready_workers=ready,
                    running_workers=running,
                )

                return True

        except Exception as e:
            logger.error(f"RunPod connection test failed: {str(e)}")
            return False

    async def list_available_models(self) -> List[Dict[str, Any]]:
        """
        List available GaMS model variants.

        GaMS models are static (not fetched from API), so this returns
        a hardcoded list of supported variants.

        Returns:
            List of dicts with model information
        """
        if self._models_cache is not None:
            return self._models_cache

        # Currently only GaMS-9B-Instruct is deployed on RunPod
        self._models_cache = [
            {
                "id": "GaMS-9B-Instruct",
                "name": "GaMS 9B Instruct",
                "description": "Native Slovenian LLM. Best balance of quality and cost.",
                "parameters": "9B",
                "base_model": "Gemma 2",
                "vram_required": "~20GB",
                "context_window": 4096,
            },
        ]

        return self._models_cache
