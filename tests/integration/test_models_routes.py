"""
Integration tests for model listing endpoints.
Tests routes without requiring authentication.
"""
import pytest
from httpx import AsyncClient


class TestTranscriptionModelsEndpoint:
    """Test GET /api/v1/models/transcription endpoint."""

    @pytest.mark.asyncio
    async def test_list_transcription_models_no_auth_required(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that transcription models endpoint doesn't require authentication."""
        # Use unauthenticated client
        async with AsyncClient(
            transport=authenticated_client._transport,
            base_url=authenticated_client.base_url
        ) as client:
            response = await client.get("/api/v1/models/transcription")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_transcription_models_returns_valid_structure(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that response has correct structure."""
        response = await authenticated_client.get("/api/v1/models/transcription")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "provider" in data
        assert "models" in data
        assert isinstance(data["provider"], str)
        assert isinstance(data["models"], list)

    @pytest.mark.asyncio
    async def test_list_transcription_models_contains_model_info(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that each model has required fields."""
        response = await authenticated_client.get("/api/v1/models/transcription")

        assert response.status_code == 200
        data = response.json()
        models = data["models"]

        assert len(models) > 0, "Should return at least one model"

        # Check first model has required fields
        first_model = models[0]
        assert "id" in first_model
        assert "name" in first_model
        assert isinstance(first_model["id"], str)
        assert isinstance(first_model["name"], str)


class TestLLMModelsEndpoint:
    """Test GET /api/v1/models/llm endpoint."""

    @pytest.mark.asyncio
    async def test_list_llm_models_no_auth_required(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that LLM models endpoint doesn't require authentication."""
        # Use unauthenticated client
        async with AsyncClient(
            transport=authenticated_client._transport,
            base_url=authenticated_client.base_url
        ) as client:
            response = await client.get("/api/v1/models/llm")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_llm_models_returns_valid_structure(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that response has correct structure."""
        response = await authenticated_client.get("/api/v1/models/llm")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "provider" in data
        assert "models" in data
        assert isinstance(data["provider"], str)
        assert isinstance(data["models"], list)

    @pytest.mark.asyncio
    async def test_list_llm_models_contains_model_info(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that each model has required fields."""
        response = await authenticated_client.get("/api/v1/models/llm")

        assert response.status_code == 200
        data = response.json()
        models = data["models"]

        assert len(models) > 0, "Should return at least one model"

        # Check first model has required fields
        first_model = models[0]
        assert "id" in first_model
        assert "name" in first_model
        assert isinstance(first_model["id"], str)
        assert isinstance(first_model["name"], str)


class TestLanguagesEndpoint:
    """Test GET /api/v1/models/languages endpoint."""

    @pytest.mark.asyncio
    async def test_list_languages_no_auth_required(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that languages endpoint doesn't require authentication."""
        # Use unauthenticated client
        async with AsyncClient(
            transport=authenticated_client._transport,
            base_url=authenticated_client.base_url
        ) as client:
            response = await client.get("/api/v1/models/languages")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_languages_returns_valid_structure(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that response has correct structure."""
        response = await authenticated_client.get("/api/v1/models/languages")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "languages" in data
        assert "count" in data
        assert isinstance(data["languages"], list)
        assert isinstance(data["count"], int)

    @pytest.mark.asyncio
    async def test_list_languages_contains_common_languages(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that response includes common languages."""
        response = await authenticated_client.get("/api/v1/models/languages")

        assert response.status_code == 200
        data = response.json()
        languages = data["languages"]

        # Should have many languages (Whisper supports 99+)
        assert len(languages) > 50, "Should support many languages"
        assert data["count"] == len(languages)

        # Check for common languages
        common_languages = ["auto", "en", "es", "fr", "de", "zh", "ja"]
        for lang in common_languages:
            assert lang in languages, f"Should include {lang}"

    @pytest.mark.asyncio
    async def test_list_languages_count_matches_list_length(
        self,
        authenticated_client: AsyncClient
    ):
        """Test that count field matches actual list length."""
        response = await authenticated_client.get("/api/v1/models/languages")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == len(data["languages"])
