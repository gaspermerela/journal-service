"""
E2E tests for model listing endpoints with real services.
These tests use the app's configured providers (Groq or local).
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e_real
class TestE2ETranscriptionModels:
    """E2E tests for transcription model listing."""

    @pytest.mark.asyncio
    async def test_e2e_list_transcription_models(
        self,
        real_api_client: AsyncClient
    ):
        """Test listing transcription models from configured provider."""
        response = await real_api_client.get("/api/v1/models/transcription")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "provider" in data
        assert "models" in data
        assert isinstance(data["provider"], str)
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0, "Should return at least one model"

    @pytest.mark.asyncio
    async def test_e2e_transcription_models_structure(
        self,
        real_api_client: AsyncClient
    ):
        """Test that transcription models have correct structure."""
        response = await real_api_client.get("/api/v1/models/transcription")

        assert response.status_code == 200
        data = response.json()

        # Verify each model has required fields
        for model in data["models"]:
            assert "id" in model
            assert "name" in model
            assert isinstance(model["id"], str)
            assert isinstance(model["name"], str)


@pytest.mark.e2e_real
class TestE2ELLMModels:
    """E2E tests for LLM model listing."""

    @pytest.mark.asyncio
    async def test_e2e_list_llm_models(
        self,
        real_api_client: AsyncClient
    ):
        """Test listing LLM models from configured provider."""
        response = await real_api_client.get("/api/v1/models/llm")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "provider" in data
        assert "models" in data
        assert isinstance(data["provider"], str)
        assert isinstance(data["models"], list)
        assert len(data["models"]) > 0, "Should return at least one model"

    @pytest.mark.asyncio
    async def test_e2e_llm_models_structure(
        self,
        real_api_client: AsyncClient
    ):
        """Test that LLM models have correct structure."""
        response = await real_api_client.get("/api/v1/models/llm")

        assert response.status_code == 200
        data = response.json()

        # Verify each model has required fields
        for model in data["models"]:
            assert "id" in model
            assert "name" in model
            assert isinstance(model["id"], str)
            assert isinstance(model["name"], str)


@pytest.mark.e2e_real
class TestE2ELanguages:
    """E2E tests for languages listing."""

    @pytest.mark.asyncio
    async def test_e2e_list_languages(
        self,
        real_api_client: AsyncClient
    ):
        """Test listing supported languages."""
        response = await real_api_client.get("/api/v1/models/languages")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "languages" in data
        assert "count" in data
        assert isinstance(data["languages"], list)
        assert isinstance(data["count"], int)

        # Whisper supports 99+ languages
        assert data["count"] >= 99, "Should support at least 99 languages"
        assert len(data["languages"]) >= 99

        # Verify count matches list length
        assert data["count"] == len(data["languages"])

        # Verify common languages are present
        common_languages = ["auto", "en", "es", "fr", "de", "it", "pt", "ru", "ja", "ko", "zh"]
        for lang in common_languages:
            assert lang in data["languages"], f"Missing common language: {lang}"
