"""
Integration tests for model listing endpoints.
Tests routes without requiring authentication.
"""
from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestUnifiedOptionsEndpoint:
    """Test GET /api/v1/options endpoint."""

    @pytest.mark.asyncio
    async def test_options_no_auth_required(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that options endpoint doesn't require authentication."""
        # Use unauthenticated client
        async with AsyncClient(
                transport=authenticated_client._transport,
                base_url=authenticated_client.base_url
        ) as client:
            response = await client.get("/api/v1/options")

            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_options_returns_valid_structure(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that response has correct structure with both transcription and LLM options."""
        response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Check top-level structure
        assert "transcription" in data
        assert "llm" in data
        assert isinstance(data["transcription"], dict)
        assert isinstance(data["llm"], dict)

        # Check transcription structure
        transcription = data["transcription"]
        assert "provider" in transcription
        assert "available_providers" in transcription
        assert "models" in transcription
        assert "parameters" in transcription
        assert isinstance(transcription["provider"], str)
        assert isinstance(transcription["available_providers"], list)
        assert isinstance(transcription["models"], list)
        assert isinstance(transcription["parameters"], dict)

        # Check LLM structure
        llm = data["llm"]
        assert "provider" in llm
        assert "available_providers" in llm
        assert "models" in llm
        assert "parameters" in llm
        assert isinstance(llm["provider"], str)
        assert isinstance(llm["available_providers"], list)
        assert isinstance(llm["models"], list)
        assert isinstance(llm["parameters"], dict)

    @pytest.mark.asyncio
    async def test_options_available_providers_contains_current(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that available_providers includes the current provider."""
        response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Current provider should be in available_providers
        transcription = data["transcription"]
        assert transcription["provider"] in transcription["available_providers"]

        llm = data["llm"]
        assert llm["provider"] in llm["available_providers"]

    @pytest.mark.asyncio
    async def test_options_available_providers_not_empty(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that available_providers is not empty (at least noop is configured)."""
        response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Should have at least one provider configured
        assert len(data["transcription"]["available_providers"]) >= 1
        assert len(data["llm"]["available_providers"]) >= 1

    @pytest.mark.asyncio
    async def test_options_transcription_models_valid(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that transcription models have required fields."""
        response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()
        models = data["transcription"]["models"]

        assert len(models) > 0, "Should return at least one transcription model"

        # Check first model has required fields
        first_model = models[0]
        assert "id" in first_model
        assert "name" in first_model
        assert isinstance(first_model["id"], str)
        assert isinstance(first_model["name"], str)

    @pytest.mark.asyncio
    async def test_options_llm_models_valid(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that LLM models have required fields."""
        response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()
        models = data["llm"]["models"]

        assert len(models) > 0, "Should return at least one LLM model"

        # Check first model has required fields
        first_model = models[0]
        assert "id" in first_model
        assert "name" in first_model
        assert isinstance(first_model["id"], str)
        assert isinstance(first_model["name"], str)

    @pytest.mark.asyncio
    async def test_options_transcription_parameters_valid(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that transcription parameters have required metadata."""
        from unittest.mock import AsyncMock, MagicMock

        # Create mock transcription service
        mock_transcription_service = MagicMock()
        mock_transcription_service.list_available_models = AsyncMock(return_value=[
            {"id": "whisper-large-v3", "name": "Whisper Large V3"}
        ])

        # Mock settings and service creation
        with patch("app.routes.models.settings") as mock_settings, \
                patch("app.routes.models.get_transcription_service_for_provider", return_value=mock_transcription_service):
            mock_settings.TRANSCRIPTION_PROVIDER = "groq"
            mock_settings.LLM_PROVIDER = "noop"

            response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()
        parameters = data["transcription"]["parameters"]

        # Groq provider should have temperature parameter
        assert "temperature" in parameters, "Groq provider should have temperature parameter"
        temp_config = parameters["temperature"]
        assert "type" in temp_config
        assert "min" in temp_config
        assert "max" in temp_config
        assert "default" in temp_config
        assert "description" in temp_config
        assert temp_config["type"] == "float"
        assert temp_config["min"] == 0.0
        assert temp_config["max"] == 1.0

    @pytest.mark.asyncio
    async def test_options_llm_parameters_valid(
            self,
            authenticated_client: AsyncClient
    ):
        """Test that LLM parameters have required metadata."""
        from unittest.mock import AsyncMock, MagicMock

        # Create mock LLM service
        mock_llm_service = MagicMock()
        mock_llm_service.list_available_models = AsyncMock(return_value=[
            {"id": "llama-3.3-70b-versatile", "name": "LLaMA 3.3 70B"}
        ])

        # Mock settings and service creation
        with patch("app.routes.models.settings") as mock_settings, \
                patch("app.routes.models.get_llm_service_for_provider", return_value=mock_llm_service):
            mock_settings.TRANSCRIPTION_PROVIDER = "noop"
            mock_settings.LLM_PROVIDER = "groq"

            response = await authenticated_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()
        parameters = data["llm"]["parameters"]

        # Groq LLM provider should have temperature and top_p parameters
        assert "temperature" in parameters, "Groq LLM provider should have temperature parameter"
        temp_config = parameters["temperature"]
        assert "type" in temp_config
        assert "min" in temp_config
        assert "max" in temp_config
        assert "default" in temp_config
        assert "description" in temp_config
        assert temp_config["type"] == "float"
        assert temp_config["min"] == 0.0
        assert temp_config["max"] == 2.0

        assert "top_p" in parameters, "Groq LLM provider should have top_p parameter"
        top_p_config = parameters["top_p"]
        assert "type" in top_p_config
        assert "min" in top_p_config
        assert "max" in top_p_config
        assert "default" in top_p_config
        assert "description" in top_p_config
        assert top_p_config["type"] == "float"
        assert top_p_config["min"] == 0.0
        assert top_p_config["max"] == 1.0


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
