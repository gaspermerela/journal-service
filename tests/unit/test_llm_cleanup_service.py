"""
Unit tests for LLM cleanup service.

Tests cleanup_transcription() - returns plain text with <break> → \n\n conversion.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx

from app.services.llm_cleanup_ollama import OllamaLLMCleanupService


@pytest.fixture
def cleanup_service():
    """Create OllamaLLMCleanupService instance for testing."""
    return OllamaLLMCleanupService()


@pytest.fixture
def mock_cleanup_response():
    """Factory fixture to create mock plain text cleanup responses."""
    def _create_response(cleaned_text: str):
        """Create a mock cleanup response with plain text and <break> markers."""
        return {"response": cleaned_text}
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
    async def test_cleanup_transcription_success(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test successful transcription cleanup returns plain text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response(
                "I dreamt about flying over mountains.<break>It was an amazing experience."
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="I dreamt about flying over mountains.",
            entry_type="dream"
        )

        assert "cleaned_text" in result
        # <break> should be converted to \n\n
        assert "\n\n" in result["cleaned_text"]
        assert "<break>" not in result["cleaned_text"]
        assert result["cleaned_text"] == "I dreamt about flying over mountains.\n\nIt was an amazing experience."

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
    async def test_cleanup_transcription_plain_text(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup returns plain text without requiring JSON parsing."""
        # Cleanup now returns plain text, not JSON
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response(
                "This is plain text without any special markers."
            ))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream"
        )

        assert "cleaned_text" in result
        assert result["cleaned_text"] == "This is plain text without any special markers."

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
    async def test_cleanup_different_entry_types(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with different entry types returns plain text."""
        entry_types = ["dream", "journal", "meeting", "note"]

        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Cleaned text"))
        )

        for entry_type in entry_types:
            result = await cleanup_service.cleanup_transcription(
                transcription_text="This is a test transcription.",
                entry_type=entry_type
            )

            assert "cleaned_text" in result

    @pytest.mark.asyncio
    async def test_cleanup_empty_text(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with empty transcription text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response(""))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="",
            entry_type="dream"
        )

        assert result is not None

    @pytest.mark.asyncio
    async def test_cleanup_very_long_text(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with very long transcription text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Summarized long text"))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text=" ".join(["word"] * 1000),
            entry_type="dream"
        )

        assert "cleaned_text" in result

    @pytest.mark.asyncio
    async def test_cleanup_special_characters(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with special characters returns plain text."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("I dreamt about stars and galaxies."))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="I dreamt about 🌟 stars & galaxies! #amazing?",
            entry_type="dream"
        )

        assert "cleaned_text" in result

    @pytest.mark.asyncio
    async def test_cleanup_with_temperature(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with custom temperature parameter."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Cleaned text with custom temperature"))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
            temperature=0.7
        )

        # Verify temperature was passed to Ollama API
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.7

        # Verify temperature is in result
        assert result["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_cleanup_with_top_p(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with custom top_p parameter."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Cleaned text with custom top_p"))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
            top_p=0.9
        )

        # Verify top_p was passed to Ollama API
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["options"]["top_p"] == 0.9

        # Verify top_p is in result
        assert result["top_p"] == 0.9

    @pytest.mark.asyncio
    async def test_cleanup_with_temperature_and_top_p(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup with both temperature and top_p parameters."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Cleaned text with both parameters"))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
            temperature=0.5,
            top_p=0.8
        )

        # Verify both parameters were passed to Ollama API
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.5
        assert payload["options"]["top_p"] == 0.8

        # Verify both parameters are in result
        assert result["temperature"] == 0.5
        assert result["top_p"] == 0.8

    @pytest.mark.asyncio
    async def test_cleanup_default_temperature_when_not_provided(self, cleanup_service, mock_httpx_client, mock_cleanup_response):
        """Test cleanup uses default temperature when not provided."""
        mock_httpx_client.post.return_value = Mock(
            json=Mock(return_value=mock_cleanup_response("Cleaned text"))
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream"
        )

        # Verify default temperature (0.3) was used
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["options"]["temperature"] == 0.3

        # Temperature in result should be None (indicates default was used)
        assert result["temperature"] is None
