"""
Unit tests for RunPod GaMS LLM cleanup service.

Tests cleanup_transcription() - returns plain text with <break> → \n\n conversion.
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
import httpx

from app.services.llm_cleanup_runpod_gams import RunPodGamsLLMCleanupService
from app.services.llm_cleanup_base import LLMCleanupError


@pytest.fixture
def mock_settings():
    """Mock settings with valid configuration."""
    mock = MagicMock()
    mock.RUNPOD_API_KEY = "test-api-key"
    mock.RUNPOD_LLM_GAMS_ENDPOINT_ID = "test-endpoint-id"
    mock.RUNPOD_LLM_GAMS_MODEL = "GaMS-9B-Instruct"
    mock.RUNPOD_LLM_GAMS_TIMEOUT = 120
    mock.RUNPOD_LLM_GAMS_MAX_RETRIES = 3
    mock.RUNPOD_LLM_GAMS_DEFAULT_TEMPERATURE = 0.0
    mock.RUNPOD_LLM_GAMS_DEFAULT_TOP_P = 0.0
    mock.RUNPOD_LLM_GAMS_MAX_TOKENS = 2048
    return mock


@pytest.fixture
def cleanup_service(mock_settings):
    """Create RunPodGamsLLMCleanupService instance for testing."""
    with patch("app.services.llm_cleanup_runpod_gams.settings", mock_settings):
        return RunPodGamsLLMCleanupService()


@pytest.fixture
def mock_runpod_response():
    """Factory fixture to create mock RunPod responses."""

    def _create_response(
        text: str,
        status: str = "COMPLETED",
        processing_time: float = 3.2,
        prompt_tokens: int = 150,
        completion_tokens: int = 120,
    ):
        """Create a mock RunPod response."""
        return {
            "status": status,
            "output": {
                "text": text,
                "processing_time": processing_time,
                "model_version": "gams-9b-instruct",
                "token_count": {
                    "prompt": prompt_tokens,
                    "completion": completion_tokens,
                },
            },
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


class TestRunPodGamsLLMCleanupService:
    """Test suite for RunPod GaMS LLM cleanup service."""

    @pytest.mark.asyncio
    async def test_cleanup_transcription_success(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test successful transcription cleanup returns plain text."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=mock_runpod_response(
                    "I dreamt about flying over mountains.<break>It was an amazing experience."
                )
            ),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="I dreamt about flying over mountains.",
            entry_type="dream",
        )

        assert "cleaned_text" in result
        # <break> should be converted to \n\n
        assert "\n\n" in result["cleaned_text"]
        assert "<break>" not in result["cleaned_text"]
        assert (
            result["cleaned_text"]
            == "I dreamt about flying over mountains.\n\nIt was an amazing experience."
        )

    @pytest.mark.asyncio
    async def test_cleanup_transcription_timeout(
        self, cleanup_service, mock_httpx_client, mock_settings
    ):
        """Test timeout handling."""
        mock_httpx_client.post.side_effect = httpx.TimeoutException("Request timed out")

        # Set max_retries to 0 to fail immediately
        with patch("app.services.llm_cleanup_runpod_gams.settings", mock_settings):
            cleanup_service.max_retries = 0

            with pytest.raises(LLMCleanupError) as exc_info:
                await cleanup_service.cleanup_transcription(
                    transcription_text="Test text",
                    entry_type="dream",
                )

            assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup_transcription_http_error(
        self, cleanup_service, mock_httpx_client
    ):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_httpx_client.post.side_effect = httpx.HTTPStatusError(
            "500 Server Error", request=Mock(), response=mock_response
        )

        cleanup_service.max_retries = 0

        with pytest.raises(LLMCleanupError):
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream",
            )

    @pytest.mark.asyncio
    async def test_cleanup_transcription_with_temperature(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test cleanup with custom temperature parameter."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=mock_runpod_response("Cleaned text with custom temperature")
            ),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
            temperature=0.7,
        )

        # Verify temperature was passed to RunPod API
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["input"]["temperature"] == 0.7

        # Verify temperature is in result
        assert result["temperature"] == 0.7

    @pytest.mark.asyncio
    async def test_cleanup_transcription_with_top_p(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test cleanup with custom top_p parameter."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_runpod_response("Cleaned text with custom top_p")),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
            top_p=0.95,
        )

        # Verify top_p was passed to RunPod API
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["input"]["top_p"] == 0.95

        # Verify top_p is in result
        assert result["top_p"] == 0.95

    @pytest.mark.asyncio
    async def test_cleanup_transcription_default_parameters(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test cleanup uses default parameters when not provided."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_runpod_response("Cleaned text")),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
        )

        # Verify defaults were used (0.0 temperature, 0.0 top_p)
        call_args = mock_httpx_client.post.call_args
        payload = call_args[1]["json"]
        assert payload["input"]["temperature"] == 0.0
        assert payload["input"]["top_p"] == 0.0

        # Result should have None for parameters (indicates defaults used)
        assert result["temperature"] is None
        assert result["top_p"] is None

    @pytest.mark.asyncio
    async def test_cleanup_transcription_runpod_job_failed(
        self, cleanup_service, mock_httpx_client
    ):
        """Test handling of RunPod job failure."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "status": "FAILED",
                    "error": "Worker crashed",
                }
            ),
            raise_for_status=Mock(),
        )

        cleanup_service.max_retries = 0

        with pytest.raises(LLMCleanupError) as exc_info:
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream",
            )

        assert "RunPod job failed" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_cleanup_transcription_handler_error(
        self, cleanup_service, mock_httpx_client
    ):
        """Test handling of GaMS handler error."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "status": "COMPLETED",
                    "output": {"error": "Model loading failed"},
                }
            ),
            raise_for_status=Mock(),
        )

        cleanup_service.max_retries = 0

        with pytest.raises(LLMCleanupError) as exc_info:
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream",
            )

        assert "handler error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup_transcription_empty_response(
        self, cleanup_service, mock_httpx_client
    ):
        """Test handling of empty response from handler."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "status": "COMPLETED",
                    "output": {"text": ""},
                }
            ),
            raise_for_status=Mock(),
        )

        cleanup_service.max_retries = 0

        with pytest.raises(LLMCleanupError) as exc_info:
            await cleanup_service.cleanup_transcription(
                transcription_text="Test text",
                entry_type="dream",
            )

        assert "empty response" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_cleanup_different_entry_types(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test cleanup with different entry types returns plain text."""
        entry_types = ["dream", "journal", "meeting", "note"]

        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(return_value=mock_runpod_response("Cleaned text")),
            raise_for_status=Mock(),
        )

        for entry_type in entry_types:
            result = await cleanup_service.cleanup_transcription(
                transcription_text="This is a test transcription.",
                entry_type=entry_type,
            )

            assert "cleaned_text" in result

    @pytest.mark.asyncio
    async def test_break_marker_conversion(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test that <break> markers are properly converted to double newlines."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=mock_runpod_response(
                    "First paragraph.<break>Second paragraph.<break>Third paragraph."
                )
            ),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
        )

        assert (
            result["cleaned_text"]
            == "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        )
        assert "<break>" not in result["cleaned_text"]

    @pytest.mark.asyncio
    async def test_excessive_newlines_normalized(
        self, cleanup_service, mock_httpx_client, mock_runpod_response
    ):
        """Test that excessive newlines are normalized to double newlines."""
        mock_httpx_client.post.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value=mock_runpod_response(
                    "First paragraph.\n\n\n\n\nSecond paragraph."
                )
            ),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.cleanup_transcription(
            transcription_text="Test text",
            entry_type="dream",
        )

        # Should normalize to exactly 2 newlines
        assert result["cleaned_text"] == "First paragraph.\n\nSecond paragraph."
        assert "\n\n\n" not in result["cleaned_text"]


class TestRunPodGamsServiceInitialization:
    """Test service initialization and configuration."""

    def test_init_requires_api_key(self, mock_settings):
        """Test that API key is required."""
        mock_settings.RUNPOD_API_KEY = None

        with patch("app.services.llm_cleanup_runpod_gams.settings", mock_settings):
            with pytest.raises(ValueError, match="RUNPOD_API_KEY is required"):
                RunPodGamsLLMCleanupService()

    def test_init_requires_endpoint_id(self, mock_settings):
        """Test that endpoint ID is required."""
        mock_settings.RUNPOD_LLM_GAMS_ENDPOINT_ID = None

        with patch("app.services.llm_cleanup_runpod_gams.settings", mock_settings):
            with pytest.raises(ValueError, match="RUNPOD_LLM_GAMS_ENDPOINT_ID is required"):
                RunPodGamsLLMCleanupService()

    def test_get_model_name(self, cleanup_service):
        """Test get_model_name returns correct format."""
        assert cleanup_service.get_model_name() == "runpod_llm_gams-GaMS-9B-Instruct"

    def test_get_provider_name(self, cleanup_service):
        """Test get_provider_name returns correct value."""
        assert cleanup_service.get_provider_name() == "runpod_llm_gams"


class TestRunPodGamsServiceModels:
    """Test model listing functionality."""

    @pytest.mark.asyncio
    async def test_list_available_models(self, cleanup_service):
        """Test list_available_models returns expected models."""
        models = await cleanup_service.list_available_models()

        # Only GaMS-9B-Instruct is currently supported
        assert len(models) == 1
        model_ids = [m["id"] for m in models]
        assert "GaMS-9B-Instruct" in model_ids

    @pytest.mark.asyncio
    async def test_list_available_models_cached(self, cleanup_service):
        """Test that models are cached after first call."""
        models1 = await cleanup_service.list_available_models()
        models2 = await cleanup_service.list_available_models()

        assert models1 is models2  # Same object reference


class TestRunPodGamsServiceConnection:
    """Test connection testing functionality."""

    @pytest.mark.asyncio
    async def test_test_connection_success(self, cleanup_service, mock_httpx_client):
        """Test successful connection test."""
        mock_httpx_client.get.return_value = Mock(
            status_code=200,
            json=Mock(
                return_value={
                    "workers": {"ready": 1, "running": 0},
                }
            ),
            raise_for_status=Mock(),
        )

        result = await cleanup_service.test_connection()

        assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, cleanup_service, mock_httpx_client):
        """Test connection test failure."""
        mock_httpx_client.get.side_effect = httpx.TimeoutException("Connection timeout")

        result = await cleanup_service.test_connection()

        assert result is False
