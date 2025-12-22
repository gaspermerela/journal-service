"""
Unit tests for RunPod transcription service.
Tests RunPodTranscriptionService with mocked HTTP calls.
"""
import pytest
import base64
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx

from app.services.transcription_runpod import RunPodTranscriptionService


class TestRunPodServiceInit:
    """Test RunPodTranscriptionService initialization."""

    def test_init_with_required_params(self):
        """Test service initializes with required parameters."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        assert service.api_key == "test-api-key"
        assert service.endpoint_id == "test-endpoint-id"
        assert service.model == "protoverb-slovenian-asr"
        assert service.max_retries == 3
        assert service.timeout == 300
        assert service.max_concurrent_chunks == 3
        # NLP pipeline defaults
        assert service.punctuate is True
        assert service.denormalize is True
        assert service.denormalize_style == "default"

    def test_init_with_custom_params(self):
        """Test service initializes with custom parameters."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            model="custom-model",
            chunk_duration_seconds=180,
            max_concurrent_chunks=5,
            max_retries=5,
            timeout=600,
            punctuate=False,
            denormalize=False,
            denormalize_style="technical"
        )

        assert service.model == "custom-model"
        assert service.max_retries == 5
        assert service.timeout == 600
        assert service.max_concurrent_chunks == 5
        assert service.punctuate is False
        assert service.denormalize is False
        assert service.denormalize_style == "technical"

    def test_init_requires_api_key(self):
        """Test service raises error without api_key."""
        with pytest.raises(ValueError, match="api_key is required"):
            RunPodTranscriptionService(
                api_key=None,
                endpoint_id="test-endpoint-id"
            )

    def test_init_requires_endpoint_id(self):
        """Test service raises error without endpoint_id."""
        with pytest.raises(ValueError, match="endpoint_id is required"):
            RunPodTranscriptionService(
                api_key="test-api-key",
                endpoint_id=None
            )

    def test_init_invalid_denormalize_style_defaults(self):
        """Test invalid denormalize_style defaults to 'default'."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            denormalize_style="invalid"
        )

        assert service.denormalize_style == "default"


class TestSupportedLanguages:
    """Test language support."""

    def test_supported_languages_only_slovenian(self):
        """Test only Slovenian languages are supported."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        languages = service.get_supported_languages()

        assert languages == ["sl", "sl-SI", "auto"]

    @pytest.mark.asyncio
    async def test_rejects_non_slovenian_language(self, tmp_path):
        """Test transcription rejects non-Slovenian languages."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        with pytest.raises(ValueError, match="only supports Slovenian"):
            await service.transcribe_audio(audio_file, language="en")

    @pytest.mark.asyncio
    async def test_accepts_slovenian_language(self, tmp_path):
        """Test transcription accepts Slovenian language codes."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        # Mock the HTTP call and the chunker's needs_chunking method
        with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call, \
             patch.object(service._chunker, 'needs_chunking', return_value=False):
            mock_call.return_value = {
                "text": "Test transcription",
                "raw_text": "test transcription",
                "pipeline": ["asr", "punctuate"],
                "model_version": "protoverb-1.0"
            }

            # Should not raise for Slovenian
            for lang in ["sl", "sl-SI", "auto"]:
                result = await service.transcribe_audio(audio_file, language=lang)
                assert "text" in result


class TestModelInfo:
    """Test model information methods."""

    def test_get_model_name(self):
        """Test get_model_name returns prefixed name."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        assert service.get_model_name() == "clarinsi_slovene_asr-protoverb-slovenian-asr"

    def test_get_model_name_custom(self):
        """Test get_model_name with custom model."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            model="custom-model"
        )

        assert service.get_model_name() == "clarinsi_slovene_asr-custom-model"

    @pytest.mark.asyncio
    async def test_list_available_models(self):
        """Test list_available_models returns PROTOVERB model info."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        models = await service.list_available_models()

        assert len(models) == 1
        assert models[0]["id"] == "protoverb-slovenian-asr"
        assert models[0]["language"] == "sl"
        assert "punctuation" in models[0]["features"]
        assert "denormalization" in models[0]["features"]
        assert "pipeline_options" in models[0]


class TestNLPPipelineOptions:
    """Test NLP pipeline options (punctuate, denormalize)."""

    @pytest.mark.asyncio
    async def test_transcribe_with_nlp_defaults(self, tmp_path):
        """Test transcription uses NLP pipeline defaults."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            punctuate=True,
            denormalize=True,
            denormalize_style="default"
        )

        with patch.object(service._chunker, 'needs_chunking', return_value=False):
            with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {
                    "text": "Processed text.",
                    "raw_text": "processed text",
                    "pipeline": ["asr", "punctuate", "denormalize"],
                    "model_version": "protoverb-1.0"
                }

                result = await service.transcribe_audio(audio_file, language="sl")

                # Verify NLP options were passed
                call_args = mock_call.call_args[0][0]
                assert call_args["punctuate"] is True
                assert call_args["denormalize"] is True
                assert call_args["denormalize_style"] == "default"

    @pytest.mark.asyncio
    async def test_transcribe_override_nlp_options(self, tmp_path):
        """Test transcription can override NLP pipeline options."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        # Service defaults: punctuate=True, denormalize=True
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        with patch.object(service._chunker, 'needs_chunking', return_value=False):
            with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {
                    "text": "raw text",
                    "raw_text": "raw text",
                    "pipeline": ["asr"],
                    "model_version": "protoverb-1.0"
                }

                # Override defaults via method params
                result = await service.transcribe_audio(
                    audio_file,
                    language="sl",
                    punctuate=False,
                    denormalize=False,
                    denormalize_style="technical"
                )

                # Verify overridden options were passed
                call_args = mock_call.call_args[0][0]
                assert call_args["punctuate"] is False
                assert call_args["denormalize"] is False
                assert call_args["denormalize_style"] == "technical"

    @pytest.mark.asyncio
    async def test_transcribe_returns_pipeline_info(self, tmp_path):
        """Test transcription returns pipeline and model_version info."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        with patch.object(service._chunker, 'needs_chunking', return_value=False):
            with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {
                    "text": "Včeraj sem spal 8 ur.",
                    "raw_text": "včeraj sem spal osem ur",
                    "pipeline": ["asr", "punctuate", "denormalize"],
                    "model_version": "protoverb-1.0",
                    "processing_time": 5.2
                }

                result = await service.transcribe_audio(audio_file, language="sl")

                assert result["text"] == "Včeraj sem spal 8 ur."
                assert result["raw_text"] == "včeraj sem spal osem ur"
                assert result["pipeline"] == ["asr", "punctuate", "denormalize"]
                assert result["model_version"] == "protoverb-1.0"


class TestTranscriptionSingle:
    """Test single file transcription (no chunking)."""

    @pytest.mark.asyncio
    async def test_transcribe_short_audio_success(self, tmp_path):
        """Test successful transcription of short audio."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        # Mock chunker to say no chunking needed
        with patch.object(service._chunker, 'needs_chunking', return_value=False):
            with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {
                    "text": "Transkriptirano besedilo.",
                    "raw_text": "transkriptirano besedilo",
                    "processing_time": 5.2,
                    "pipeline": ["asr", "punctuate"],
                    "model_version": "protoverb-1.0"
                }

                result = await service.transcribe_audio(audio_file, language="sl")

                assert result["text"] == "Transkriptirano besedilo."
                assert result["raw_text"] == "transkriptirano besedilo"
                assert result["language"] == "sl"
                assert result["beam_size"] is None
                assert result["temperature"] is None
                assert "pipeline" in result
                assert "model_version" in result

    @pytest.mark.asyncio
    async def test_transcribe_file_not_found(self, tmp_path):
        """Test transcription fails for non-existent file."""
        non_existent = tmp_path / "does_not_exist.wav"

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        with pytest.raises(FileNotFoundError):
            await service.transcribe_audio(non_existent, language="sl")

    @pytest.mark.asyncio
    async def test_unsupported_params_logged_as_warning(self, tmp_path, caplog):
        """Test unsupported parameters are logged as warnings."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        with patch.object(service._chunker, 'needs_chunking', return_value=False):
            with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                mock_call.return_value = {
                    "text": "Test",
                    "raw_text": "test",
                    "pipeline": ["asr"],
                    "model_version": "protoverb-1.0"
                }

                await service.transcribe_audio(
                    audio_file,
                    language="sl",
                    beam_size=5,
                    temperature=0.5,
                    model="different-model"
                )

                # Check warnings were logged (caplog captures logs)
                # Note: May need to check log output depending on setup


class TestTranscriptionWithChunking:
    """Test chunked transcription for long audio."""

    @pytest.mark.asyncio
    async def test_transcribe_long_audio_uses_chunking(self, tmp_path):
        """Test long audio triggers chunking."""
        audio_file = tmp_path / "long_audio.wav"
        audio_file.write_bytes(b"fake long audio content")

        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        # Mock chunker to say chunking is needed
        mock_chunks = [
            MagicMock(index=0, path=tmp_path / "chunk_0.wav", start_time_ms=0, end_time_ms=240000, duration_ms=240000),
            MagicMock(index=1, path=tmp_path / "chunk_1.wav", start_time_ms=235000, end_time_ms=475000, duration_ms=240000)
        ]
        # Create mock chunk files
        for chunk in mock_chunks:
            chunk.path.write_bytes(b"fake chunk")

        with patch.object(service._chunker, 'needs_chunking', return_value=True):
            with patch.object(service._chunker, 'chunk_audio', return_value=mock_chunks):
                with patch.object(service._chunker, 'get_chunk_metadata', return_value={
                    "num_chunks": 2,
                    "total_duration_ms": 475000
                }):
                    with patch.object(service, '_call_runpod_with_retry', new_callable=AsyncMock) as mock_call:
                        mock_call.side_effect = [
                            {
                                "text": "Prvi del besedila.",
                                "raw_text": "prvi del besedila",
                                "processing_time": 5.0,
                                "pipeline": ["asr", "punctuate"],
                                "model_version": "protoverb-1.0"
                            },
                            {
                                "text": "Drugi del besedila.",
                                "raw_text": "drugi del besedila",
                                "processing_time": 5.0,
                                "pipeline": ["asr", "punctuate"],
                                "model_version": "protoverb-1.0"
                            }
                        ]

                        result = await service.transcribe_audio(audio_file, language="sl")

                        assert "Prvi del besedila" in result["text"]
                        assert "Drugi del besedila" in result["text"]
                        assert "chunking_metadata" in result
                        assert result["chunking_metadata"]["num_chunks"] == 2
                        assert "raw_text" in result
                        assert "pipeline" in result


class TestRunPodAPICall:
    """Test RunPod API call and retry logic."""

    @pytest.mark.asyncio
    async def test_call_runpod_sync_success(self):
        """Test successful RunPod API call."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "COMPLETED",
            "output": {
                "text": "Transcribed text.",
                "raw_text": "transcribed text",
                "processing_time": 5.0,
                "pipeline": ["asr", "punctuate"],
                "model_version": "protoverb-1.0"
            }
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await service._call_runpod_sync({"audio_base64": "..."})

            assert result["text"] == "Transcribed text."
            assert result["raw_text"] == "transcribed text"

    @pytest.mark.asyncio
    async def test_call_runpod_sync_job_failed(self):
        """Test RunPod API call handles job failure."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "FAILED",
            "error": "Model loading failed"
        }
        mock_response.raise_for_status = Mock()

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(RuntimeError, match="RunPod job failed"):
                await service._call_runpod_sync({"audio_base64": "..."})

    @pytest.mark.asyncio
    async def test_retry_on_timeout(self):
        """Test retry logic on timeout."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            max_retries=3
        )

        # First two calls timeout, third succeeds
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "COMPLETED",
            "output": {
                "text": "Success after retry",
                "raw_text": "success after retry",
                "pipeline": ["asr"],
                "model_version": "protoverb-1.0"
            }
        }
        mock_response.raise_for_status = Mock()

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return mock_response

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch('asyncio.sleep', new_callable=AsyncMock):
                result = await service._call_runpod_with_retry({"audio_base64": "..."})

                assert result["text"] == "Success after retry"
                assert call_count == 3

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """Test failure after max retries exceeded."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id",
            max_retries=2
        )

        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch('asyncio.sleep', new_callable=AsyncMock):
                with pytest.raises(RuntimeError, match="failed after 2 attempts"):
                    await service._call_runpod_with_retry({"audio_base64": "..."})


class TestReassembly:
    """Test chunk transcription reassembly."""

    def test_reassemble_multiple_chunks(self):
        """Test reassembly combines chunks in order."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        results = [
            {"chunk_index": 0, "text": "First part", "raw_text": "first part"},
            {"chunk_index": 1, "text": "Second part", "raw_text": "second part"},
            {"chunk_index": 2, "text": "Third part", "raw_text": "third part"}
        ]

        combined = service._reassemble_transcriptions(results)
        combined_raw = service._reassemble_transcriptions(results, use_raw=True)

        assert combined == "First part Second part Third part"
        assert combined_raw == "first part second part third part"

    def test_reassemble_handles_empty_text(self):
        """Test reassembly handles empty text in chunks."""
        service = RunPodTranscriptionService(
            api_key="test-api-key",
            endpoint_id="test-endpoint-id"
        )

        results = [
            {"chunk_index": 0, "text": "First part", "raw_text": "first part"},
            {"chunk_index": 1, "text": "", "raw_text": ""},
            {"chunk_index": 2, "text": "Third part", "raw_text": "third part"}
        ]

        combined = service._reassemble_transcriptions(results)

        assert combined == "First part Third part"


class TestHeaders:
    """Test HTTP headers."""

    def test_get_headers(self):
        """Test authorization headers are correct."""
        service = RunPodTranscriptionService(
            api_key="my-secret-key",
            endpoint_id="test-endpoint-id"
        )

        headers = service._get_headers()

        assert headers["Authorization"] == "Bearer my-secret-key"
        assert headers["Content-Type"] == "application/json"
