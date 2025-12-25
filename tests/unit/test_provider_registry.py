"""
Unit tests for provider registry with runpods support.
Tests the new multi-model provider architecture for clarin-slovene-asr.
"""
from unittest.mock import patch, MagicMock

import pytest

from app.services.provider_registry import (
    TRANSCRIPTION_PROVIDERS,
    is_transcription_provider_configured,
    get_missing_settings_for_transcription_provider,
    get_available_runpods_for_provider,
    get_transcription_service_for_provider,
    get_available_transcription_providers,
)


class TestTranscriptionProvidersConfig:
    """Test TRANSCRIPTION_PROVIDERS configuration structure."""

    def test_clarin_slovene_asr_has_runpods(self):
        """Test clarin-slovene-asr provider has runpods config."""
        assert "clarin-slovene-asr" in TRANSCRIPTION_PROVIDERS
        provider = TRANSCRIPTION_PROVIDERS["clarin-slovene-asr"]
        assert "runpods" in provider
        assert isinstance(provider["runpods"], dict)

    def test_clarin_slovene_asr_has_all_variants(self):
        """Test clarin-slovene-asr has nfa, mms, pyannote runpods."""
        runpods = TRANSCRIPTION_PROVIDERS["clarin-slovene-asr"]["runpods"]
        assert "nfa" in runpods
        assert "mms" in runpods
        assert "pyannote" in runpods

    def test_runpod_config_has_required_fields(self):
        """Test each runpod config has endpoint_setting and description."""
        runpods = TRANSCRIPTION_PROVIDERS["clarin-slovene-asr"]["runpods"]
        for runpod_id, config in runpods.items():
            assert "endpoint_setting" in config, f"{runpod_id} missing endpoint_setting"
            assert "description" in config, f"{runpod_id} missing description"

    def test_other_providers_no_runpods(self):
        """Test other providers don't have runpods config."""
        for provider_name, config in TRANSCRIPTION_PROVIDERS.items():
            if provider_name != "clarin-slovene-asr":
                assert "runpods" not in config, f"{provider_name} should not have runpods"


class TestIsTranscriptionProviderConfigured:
    """Test is_transcription_provider_configured with runpods."""

    def test_unknown_provider_returns_false(self):
        """Test unknown provider returns False."""
        assert is_transcription_provider_configured("unknown-provider") is False

    def test_groq_configured_when_api_key_set(self):
        """Test groq is configured when GROQ_API_KEY is set."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = "test-key"

        with patch('app.services.provider_registry.settings', mock_settings):
            assert is_transcription_provider_configured("groq") is True

    def test_groq_not_configured_when_api_key_empty(self):
        """Test groq is not configured when GROQ_API_KEY is empty."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            assert is_transcription_provider_configured("groq") is False

    def test_slovene_asr_requires_runpod_api_key(self):
        """Test clarin-slovene-asr requires RUNPOD_API_KEY."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = ""
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "endpoint-123"

        with patch('app.services.provider_registry.settings', mock_settings):
            # Should fail because RUNPOD_API_KEY is empty
            assert is_transcription_provider_configured("clarin-slovene-asr") is False

    def test_slovene_asr_requires_at_least_one_endpoint(self):
        """Test clarin-slovene-asr requires at least one endpoint configured."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            # Should fail because no endpoints configured
            assert is_transcription_provider_configured("clarin-slovene-asr") is False

    def test_slovene_asr_configured_with_one_endpoint(self):
        """Test clarin-slovene-asr is configured with just one endpoint."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "endpoint-123"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            assert is_transcription_provider_configured("clarin-slovene-asr") is True

    def test_slovene_asr_configured_with_all_endpoints(self):
        """Test clarin-slovene-asr is configured with all endpoints."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = "mms-endpoint"
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = "pyannote-endpoint"

        with patch('app.services.provider_registry.settings', mock_settings):
            assert is_transcription_provider_configured("clarin-slovene-asr") is True

    def test_noop_always_configured(self):
        """Test noop provider is always configured."""
        assert is_transcription_provider_configured("noop") is True


class TestGetMissingSettingsForTranscriptionProvider:
    """Test get_missing_settings_for_transcription_provider."""

    def test_unknown_provider_returns_empty(self):
        """Test unknown provider returns empty list."""
        assert get_missing_settings_for_transcription_provider("unknown") == []

    def test_fully_configured_returns_empty(self):
        """Test fully configured provider returns empty list."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = "test-key"

        with patch('app.services.provider_registry.settings', mock_settings):
            missing = get_missing_settings_for_transcription_provider("groq")
            assert missing == []

    def test_slovene_asr_missing_api_key(self):
        """Test clarin-slovene-asr reports missing RUNPOD_API_KEY."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = ""
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "endpoint-123"

        with patch('app.services.provider_registry.settings', mock_settings):
            missing = get_missing_settings_for_transcription_provider("clarin-slovene-asr")
            assert "RUNPOD_API_KEY" in missing

    def test_slovene_asr_missing_all_endpoints(self):
        """Test clarin-slovene-asr reports missing endpoints."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            missing = get_missing_settings_for_transcription_provider("clarin-slovene-asr")
            # Should report that at least one endpoint is needed
            assert len(missing) == 1
            assert "At least one of:" in missing[0]
            assert "SLOVENE_ASR_NFA_ENDPOINT_ID" in missing[0]


class TestGetAvailableRunpodsForProvider:
    """Test get_available_runpods_for_provider."""

    def test_unknown_provider_returns_empty(self):
        """Test unknown provider returns empty list."""
        assert get_available_runpods_for_provider("unknown") == []

    def test_provider_without_runpods_returns_empty(self):
        """Test provider without runpods returns empty list."""
        assert get_available_runpods_for_provider("groq") == []

    def test_no_endpoints_configured(self):
        """Test returns empty when no endpoints configured."""
        mock_settings = MagicMock()
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            runpods = get_available_runpods_for_provider("clarin-slovene-asr")
            assert runpods == []

    def test_one_endpoint_configured(self):
        """Test returns only configured endpoint."""
        mock_settings = MagicMock()
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            runpods = get_available_runpods_for_provider("clarin-slovene-asr")
            assert len(runpods) == 1
            assert runpods[0]["id"] == "nfa"
            assert "description" in runpods[0]

    def test_all_endpoints_configured(self):
        """Test returns all configured endpoints."""
        mock_settings = MagicMock()
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = "mms-endpoint"
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = "pyannote-endpoint"

        with patch('app.services.provider_registry.settings', mock_settings):
            runpods = get_available_runpods_for_provider("clarin-slovene-asr")
            assert len(runpods) == 3
            ids = [r["id"] for r in runpods]
            assert "nfa" in ids
            assert "mms" in ids
            assert "pyannote" in ids


class TestGetTranscriptionServiceForProvider:
    """Test get_transcription_service_for_provider with model parameter."""

    def test_unknown_provider_raises(self):
        """Test unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unknown transcription provider"):
            get_transcription_service_for_provider("unknown-provider")

    def test_unconfigured_provider_raises(self):
        """Test unconfigured provider raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            with pytest.raises(ValueError, match="not configured"):
                get_transcription_service_for_provider("groq")

    def test_noop_provider_returns_service(self):
        """Test noop provider returns NoOpTranscriptionService."""
        service = get_transcription_service_for_provider("noop")
        assert service is not None
        assert service.get_model_name() == "noop-whisper-test"

    def test_slovene_asr_uses_first_available_when_no_model(self):
        """Test clarin-slovene-asr uses first available runpod when no model specified."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = "mms-endpoint"
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""
        # Add other required settings
        mock_settings.RUNPOD_CHUNK_DURATION_SECONDS = 240
        mock_settings.RUNPOD_CHUNK_OVERLAP_SECONDS = 5
        mock_settings.RUNPOD_USE_SILENCE_DETECTION = True
        mock_settings.RUNPOD_MAX_CONCURRENT_CHUNKS = 3
        mock_settings.RUNPOD_MAX_RETRIES = 3
        mock_settings.RUNPOD_TIMEOUT = 300
        mock_settings.RUNPOD_PUNCTUATE = True
        mock_settings.RUNPOD_DENORMALIZE = True
        mock_settings.RUNPOD_DENORMALIZE_STYLE = "default"

        with patch('app.services.provider_registry.settings', mock_settings):
            service = get_transcription_service_for_provider("clarin-slovene-asr")
            # Should use mms since it's the only one configured
            assert service.variant == "mms"

    def test_slovene_asr_with_specific_model(self):
        """Test clarin-slovene-asr with specific model parameter."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = "mms-endpoint"
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = "pyannote-endpoint"
        # Add other required settings
        mock_settings.RUNPOD_CHUNK_DURATION_SECONDS = 240
        mock_settings.RUNPOD_CHUNK_OVERLAP_SECONDS = 5
        mock_settings.RUNPOD_USE_SILENCE_DETECTION = True
        mock_settings.RUNPOD_MAX_CONCURRENT_CHUNKS = 3
        mock_settings.RUNPOD_MAX_RETRIES = 3
        mock_settings.RUNPOD_TIMEOUT = 300
        mock_settings.RUNPOD_PUNCTUATE = True
        mock_settings.RUNPOD_DENORMALIZE = True
        mock_settings.RUNPOD_DENORMALIZE_STYLE = "default"

        with patch('app.services.provider_registry.settings', mock_settings):
            service = get_transcription_service_for_provider("clarin-slovene-asr", model="pyannote")
            assert service.variant == "pyannote"

    def test_slovene_asr_unknown_model_raises(self):
        """Test clarin-slovene-asr with unknown model raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"

        with patch('app.services.provider_registry.settings', mock_settings):
            with pytest.raises(ValueError, match="Unknown model 'invalid'"):
                get_transcription_service_for_provider("clarin-slovene-asr", model="invalid")

    def test_slovene_asr_unconfigured_model_raises(self):
        """Test clarin-slovene-asr with unconfigured model raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""  # Not configured
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            with pytest.raises(ValueError, match="is not configured"):
                get_transcription_service_for_provider("clarin-slovene-asr", model="mms")

    def test_slovene_asr_no_endpoints_raises(self):
        """Test clarin-slovene-asr with no endpoints configured raises ValueError."""
        mock_settings = MagicMock()
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            with pytest.raises(ValueError, match="not configured"):
                get_transcription_service_for_provider("clarin-slovene-asr")


class TestGetAvailableTranscriptionProviders:
    """Test get_available_transcription_providers."""

    def test_returns_configured_providers_only(self):
        """Test returns only providers that are fully configured."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = "test-key"
        mock_settings.ASSEMBLYAI_API_KEY = ""
        mock_settings.RUNPOD_API_KEY = "test-key"
        mock_settings.SLOVENE_ASR_NFA_ENDPOINT_ID = "nfa-endpoint"
        mock_settings.SLOVENE_ASR_MMS_ENDPOINT_ID = ""
        mock_settings.SLOVENE_ASR_PYANNOTE_ENDPOINT_ID = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            providers = get_available_transcription_providers()
            assert "groq" in providers
            assert "clarin-slovene-asr" in providers
            assert "noop" in providers
            assert "assemblyai" not in providers

    def test_noop_always_available(self):
        """Test noop is always available."""
        mock_settings = MagicMock()
        mock_settings.GROQ_API_KEY = ""
        mock_settings.ASSEMBLYAI_API_KEY = ""
        mock_settings.RUNPOD_API_KEY = ""

        with patch('app.services.provider_registry.settings', mock_settings):
            providers = get_available_transcription_providers()
            assert "noop" in providers


class TestCaseInsensitivity:
    """Test provider names are case-insensitive."""

    def test_is_configured_case_insensitive(self):
        """Test is_transcription_provider_configured is case-insensitive."""
        assert is_transcription_provider_configured("NOOP") is True
        assert is_transcription_provider_configured("Noop") is True
        assert is_transcription_provider_configured("noop") is True

    def test_get_available_runpods_case_insensitive(self):
        """Test get_available_runpods_for_provider is case-insensitive."""
        # Should not raise, even with uppercase
        result = get_available_runpods_for_provider("CLARIN-SLOVENE-ASR")
        # Result depends on settings, but it shouldn't raise
        assert isinstance(result, list)

    def test_get_service_case_insensitive(self):
        """Test get_transcription_service_for_provider is case-insensitive."""
        service = get_transcription_service_for_provider("NOOP")
        assert service is not None

        service2 = get_transcription_service_for_provider("Noop")
        assert service2 is not None
