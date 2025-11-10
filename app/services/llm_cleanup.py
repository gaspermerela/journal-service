"""
LLM Cleanup Service for processing transcriptions using Ollama.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

import httpx

from app.config import settings


logger = logging.getLogger(__name__)


# Prompt templates for different entry types
DREAM_CLEANUP_PROMPT = """You are a dream journal assistant. Clean up this voice transcription of a dream:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and emotional tone intact
5. Extract key themes (max 5)
6. Identify emotions present
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["theme1", "theme2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}"""


GENERIC_CLEANUP_PROMPT = """You are a transcription cleanup assistant. Clean up this voice transcription:

Original transcription:
{transcription_text}

Tasks:
1. Fix grammar, punctuation, and capitalization
2. Remove filler words (um, uh, like, you know)
3. Organize into coherent paragraphs
4. Keep the original meaning and tone intact
5. Extract key topics or themes (max 5)
6. Identify the overall sentiment or emotions
7. Note any people/entities mentioned
8. Note any locations mentioned

Respond ONLY with valid JSON in this exact format (no markdown, no extra text):
{{
  "cleaned_text": "The cleaned version here",
  "themes": ["topic1", "topic2"],
  "emotions": ["emotion1", "emotion2"],
  "characters": ["person or entity"],
  "locations": ["place mentioned"]
}}"""


class LLMCleanupService:
    """Service for cleaning transcriptions using local LLM (Ollama)."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.LLM_TIMEOUT_SECONDS
        self.max_retries = settings.LLM_MAX_RETRIES

    def _get_prompt_template(self, entry_type: str) -> str:
        """Get the appropriate prompt template based on entry type."""
        if entry_type == "dream":
            return DREAM_CLEANUP_PROMPT
        else:
            return GENERIC_CLEANUP_PROMPT

    async def cleanup_transcription(
        self,
        transcription_text: str,
        entry_type: str = "dream"
    ) -> Dict[str, Any]:
        """
        Clean up transcription text using Ollama LLM.

        Args:
            transcription_text: Raw transcription text to clean
            entry_type: Type of entry (dream, journal, meeting, etc.)

        Returns:
            Dict containing cleaned_text and analysis

        Raises:
            Exception: If cleanup fails after retries
        """
        prompt_template = self._get_prompt_template(entry_type)
        prompt = prompt_template.format(transcription_text=transcription_text)

        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM cleanup attempt {attempt + 1}/{self.max_retries + 1} "
                    f"using model {self.model}"
                )
                result = await self._call_ollama(prompt)
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

    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """
        Call Ollama API to process the prompt.

        Args:
            prompt: Formatted prompt to send to LLM

        Returns:
            Dict containing cleaned_text and analysis

        Raises:
            httpx.HTTPError: If API call fails
            json.JSONDecodeError: If response is not valid JSON
            KeyError: If response missing required fields
        """
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,  # Lower temperature for more consistent output
                # "num_predict": 2000,  # Max tokens to generate
            }
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()
            response_text = data.get("response", "")

            logger.debug(f"Raw LLM response: {response_text[:200]}...")

            # Parse the JSON response
            result = self._parse_llm_response(response_text)

            return result

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
