"""
Unit tests for model listing service methods.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.transcription_groq import GroqTranscriptionService
from app.services.transcription_assemblyai import AssemblyAITranscriptionService
from app.services.transcription_noop import NoOpTranscriptionService
from app.services.llm_cleanup_groq import GroqLLMCleanupService
from app.services.llm_cleanup_noop import NoOpLLMCleanupService


class TestGroqTranscriptionServiceModels:
    """Test GroqTranscriptionService.list_available_models()"""

    @pytest.mark.asyncio
    async def test_list_available_models_fetches_from_groq_api(self):
        """Test that Groq service fetches models from API and filters whisper models."""
        service = GroqTranscriptionService(
            api_key="test-api-key",
            model="whisper-large-v3"
        )

        # Mock API response
        mock_response = {
            "data": [
                {
                    "id": "whisper-large-v3",
                    "owned_by": "OpenAI",
                    "context_window": 448,
                    "active": True
                },
                {
                    "id": "whisper-large-v3-turbo",
                    "owned_by": "OpenAI",
                    "context_window": 448,
                    "active": True
                },
                {
                    "id": "distil-whisper-large-v3-en",
                    "owned_by": "Hugging Face",
                    "context_window": 448,
                    "active": True
                },
                {
                    "id": "llama-3.3-70b-versatile",
                    "owned_by": "Meta",
                    "context_window": 8192,
                    "active": True
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()  # Synchronous mock for response
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            models = await service.list_available_models()

        # Should return only whisper models (filtered out llama)
        assert isinstance(models, list)
        assert len(models) == 3  # whisper-large-v3, whisper-large-v3-turbo, distil-whisper-large-v3-en

        model_ids = [m["id"] for m in models]
        assert "whisper-large-v3" in model_ids
        assert "whisper-large-v3-turbo" in model_ids
        assert "distil-whisper-large-v3-en" in model_ids
        assert "llama-3.3-70b-versatile" not in model_ids  # LLM model should be filtered out

    @pytest.mark.asyncio
    async def test_list_available_models_handles_api_error(self):
        """Test that API errors are propagated as RuntimeError."""
        service = GroqTranscriptionService(
            api_key="test-api-key",
            model="whisper-large-v3"
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("API connection failed")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="Failed to fetch Groq models"):
                await service.list_available_models()


class TestAssemblyAITranscriptionServiceModels:
    """Test AssemblyAITranscriptionService.list_available_models()"""

    @pytest.mark.asyncio
    async def test_list_available_models_returns_assemblyai_models(self):
        """Test that AssemblyAI service returns expected models."""
        service = AssemblyAITranscriptionService(
            api_key="test-api-key",
            model="universal"
        )

        models = await service.list_available_models()

        # Should return only universal model
        assert isinstance(models, list)
        assert len(models) == 1

        # Check structure of models
        assert models[0]["id"] == "universal"
        assert "name" in models[0]
        assert "description" in models[0]

    @pytest.mark.asyncio
    async def test_list_available_models_cached(self):
        """Test that models are cached after first call."""
        service = AssemblyAITranscriptionService(
            api_key="test-api-key",
            model="universal"
        )

        # First call
        models1 = await service.list_available_models()

        # Cache should be populated
        assert service._models_cache is not None
        assert service._models_cache_timestamp is not None

        # Second call should return same data from cache
        models2 = await service.list_available_models()

        assert models1 == models2


class TestNoOpTranscriptionServiceModels:
    """Test NoOpTranscriptionService.list_available_models()"""

    @pytest.mark.asyncio
    async def test_list_available_models_returns_test_model(self):
        """Test that NoOp service returns test model."""
        service = NoOpTranscriptionService()

        models = await service.list_available_models()

        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0]["id"] == "noop-whisper-test"
        assert models[0]["name"] == "NoOp Test Model"


class TestGroqLLMCleanupServiceModels:
    """Test GroqLLMCleanupService.list_available_models()"""

    @pytest.mark.asyncio
    async def test_list_available_models_fetches_from_groq_api(self):
        """Test that Groq LLM service fetches models and excludes whisper models."""
        service = GroqLLMCleanupService(
            api_key="test-api-key",
            model="llama-3.3-70b-versatile"
        )

        # Mock API response
        mock_response = {
            "data": [
                {
                    "id": "llama-3.3-70b-versatile",
                    "owned_by": "Meta",
                    "context_window": 8192,
                    "active": True
                },
                {
                    "id": "llama3-8b-8192",
                    "owned_by": "Meta",
                    "context_window": 8192,
                    "active": True
                },
                {
                    "id": "whisper-large-v3",
                    "owned_by": "OpenAI",
                    "context_window": 448,
                    "active": True
                },
                {
                    "id": "distil-whisper-large-v3-en",
                    "owned_by": "Hugging Face",
                    "context_window": 448,
                    "active": True
                }
            ]
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response_obj = MagicMock()  # Synchronous mock for response
            mock_response_obj.raise_for_status = MagicMock()
            mock_response_obj.json = MagicMock(return_value=mock_response)
            mock_client.get = AsyncMock(return_value=mock_response_obj)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            models = await service.list_available_models()

        # Should return only LLM models (filtered out whisper)
        assert isinstance(models, list)
        assert len(models) == 2  # llama-3.3-70b-versatile, llama3-8b-8192

        model_ids = [m["id"] for m in models]
        assert "llama-3.3-70b-versatile" in model_ids
        assert "llama3-8b-8192" in model_ids
        assert "whisper-large-v3" not in model_ids  # Whisper models should be filtered out
        assert "distil-whisper-large-v3-en" not in model_ids

    @pytest.mark.asyncio
    async def test_list_available_models_handles_api_error(self):
        """Test that API errors are propagated as RuntimeError."""
        service = GroqLLMCleanupService(
            api_key="test-api-key",
            model="llama-3.3-70b-versatile"
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get.side_effect = Exception("API connection failed")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError, match="Failed to fetch Groq models"):
                await service.list_available_models()


class TestNoOpLLMCleanupServiceModels:
    """Test NoOpLLMCleanupService.list_available_models()"""

    @pytest.mark.asyncio
    async def test_list_available_models_returns_test_model(self):
        """Test that NoOp service returns test model."""
        service = NoOpLLMCleanupService()

        models = await service.list_available_models()

        assert isinstance(models, list)
        assert len(models) == 1
        assert models[0]["id"] == "noop-llm-test"
        assert models[0]["name"] == "NoOp Test Model"
