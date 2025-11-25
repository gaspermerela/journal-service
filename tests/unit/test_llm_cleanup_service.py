"""
Unit tests for LLM cleanup service.
"""
import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.llm_cleanup_ollama import OllamaLLMCleanupService


@pytest.fixture
def cleanup_service():
    """Create OllamaLLMCleanupService instance for testing."""
    return OllamaLLMCleanupService()


@pytest.fixture
def mock_ollama_response():
    """Factory fixture to create mock Ollama API responses."""
    def _create_response(cleaned_text: str, themes=None, emotions=None, characters=None, locations=None):
        """Create a mock response with the given data."""
        return {
            "response": json.dumps({
                "cleaned_text": cleaned_text,
                "themes": themes or [],
                "emotions": emotions or [],
                "characters": characters or [],
                "locations": locations or []
            })
        }
    return _create_response


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.AsyncClient with proper context manager support."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        yield mock_client


class TestLLMCleanupService:
    """Test suite for LLM cleanup service."""

    @pytest.mark.asyncio
    async def test_cleanup_transcription_success(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test successful transcription cleanup."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(
                cleaned_text="I dreamt about flying over mountains.",
                themes=["flying", "nature", "freedom"],
                emotions=["wonder", "excitement"],
                locations=["mountains"]
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="I dreamt about flying over mountains.",
            entry_type="dream"
        )

        assert "cleaned_text" in result
        assert "analysis" in result
        assert result["cleaned_text"] == "I dreamt about flying over mountains."
        assert "themes" in result["analysis"]
        assert "flying" in result["analysis"]["themes"]

    @pytest.mark.asyncio
    async def test_cleanup_transcription_timeout(self, cleanup_service, mock_httpx_client):
        """Test timeout handling."""
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(Exception) as exc_info:
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream"
            )

        assert "timeout" in str(exc_info.value).lower() or "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup_transcription_invalid_json(self, cleanup_service, mock_httpx_client):
        """Test handling of invalid JSON response."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value={"response": "This is not valid JSON!"})
        )

        with pytest.raises(Exception) as exc_info:
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream"
            )

        assert "json" in str(exc_info.value).lower() or "parse" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup_transcription_http_error(self, cleanup_service, mock_httpx_client):
        """Test handling of HTTP errors."""
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "500 Server Error",
            request=Mock(),
            response=Mock(status_code=500)
        )

        with pytest.raises(Exception):
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream"
            )

    @pytest.mark.asyncio
    async def test_cleanup_different_entry_types(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test cleanup with different entry types."""
        entry_types = ["dream", "journal", "meeting", "note"]

        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(
                cleaned_text="Cleaned text",
                themes=["test"],
                emotions=["neutral"]
            ))
        )

        for entry_type in entry_types:
            result = await cleanup_service.cleanup_transcription(
                transcription_text="This is a test transcription.",
                entry_type=entry_type
            )

            assert "cleaned_text" in result
            assert "analysis" in result

    @pytest.mark.asyncio
    async def test_cleanup_empty_text(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test cleanup with empty transcription text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(cleaned_text=""))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="",
            entry_type="dream"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_cleanup_very_long_text(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test cleanup with very long transcription text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(
                cleaned_text="Summarized long text",
                themes=["repetition"],
                emotions=["neutral"]
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text=" ".join(["word"] * 1000),
            entry_type="dream"
        )

        assert "cleaned_text" in result

    @pytest.mark.asyncio
    async def test_cleanup_special_characters(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test cleanup with special characters in text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(
                cleaned_text="I dreamt about stars and galaxies.",
                themes=["space", "astronomy"],
                emotions=["wonder"],
                locations=["space"]
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="I dreamt about 🌟 stars & galaxies! #amazing?",
            entry_type="dream"
        )

        assert "cleaned_text" in result
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_cleanup_missing_analysis_fields(self, cleanup_service, mock_httpx_client, mock_ollama_response):
        """Test handling of incomplete analysis in response."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_ollama_response(
                cleaned_text="Cleaned text",
                themes=["test"]
                # emotions, characters, locations missing - will use defaults
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream"
        )

        # Should still work, even with incomplete analysis
        assert "cleaned_text" in result
        assert "analysis" in result
