"""
E2E tests for unified options endpoint.
Tests the /api/v1/options endpoint with real services.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.e2e_real
class TestE2EUnifiedOptions:
    """E2E tests for unified options endpoint."""

    @pytest.mark.asyncio
    async def test_e2e_options_endpoint_accessible(
        self,
        real_api_client: AsyncClient
    ):
        """Test that options endpoint is accessible and returns valid data."""
        response = await real_api_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Verify top-level structure
        assert "transcription" in data
        assert "llm" in data

    @pytest.mark.asyncio
    async def test_e2e_options_includes_real_providers(
        self,
        real_api_client: AsyncClient
    ):
        """Test that options endpoint returns real provider information."""
        response = await real_api_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Verify transcription provider and models
        transcription = data["transcription"]
        assert transcription["provider"] in ["whisper", "groq"]
        assert len(transcription["models"]) > 0

        # Verify LLM provider and models
        llm = data["llm"]
        assert llm["provider"] in ["ollama", "groq"]
        assert len(llm["models"]) > 0

    @pytest.mark.asyncio
    async def test_e2e_options_parameters_have_constraints(
        self,
        real_api_client: AsyncClient
    ):
        """Test that provider parameters include proper constraints."""
        response = await real_api_client.get("/api/v1/options")

        assert response.status_code == 200
        data = response.json()

        # Check transcription parameters (if any)
        transcription_params = data["transcription"]["parameters"]
        if transcription_params:
            for param_name, param_config in transcription_params.items():
                assert "type" in param_config
                assert "description" in param_config
                # Number types should have min/max
                if param_config["type"] in ["float", "int"]:
                    assert "min" in param_config
                    assert "max" in param_config

        # Check LLM parameters
        llm_params = data["llm"]["parameters"]
        if llm_params:
            for param_name, param_config in llm_params.items():
                assert "type" in param_config
                assert "description" in param_config
                if param_config["type"] in ["float", "int"]:
                    assert "min" in param_config
                    assert "max" in param_config


@pytest.mark.e2e_real
class TestE2ELanguages:
    """E2E tests for languages listing endpoint."""

    @pytest.mark.asyncio
    async def test_e2e_languages_endpoint_accessible(
        self,
        real_api_client: AsyncClient
    ):
        """Test that languages endpoint returns valid data."""
        response = await real_api_client.get("/api/v1/models/languages")

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "languages" in data
        assert "count" in data
        assert len(data["languages"]) > 50  # Whisper supports 99+ languages
        assert data["count"] == len(data["languages"])

        # Verify common languages present
        assert "auto" in data["languages"]
        assert "en" in data["languages"]
        assert "sl" in data["languages"]
