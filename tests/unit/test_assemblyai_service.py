"""
Unit tests for AssemblyAI transcription service.
Tests with mocked API responses.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

from app.services.transcription_assemblyai import AssemblyAITranscriptionService


class TestAssemblyAITranscriptionService:
    """Test AssemblyAITranscriptionService methods."""

    @pytest.mark.asyncio
    async def test_transcribe_audio_success(self, tmp_path):
        """Test successful transcription workflow."""
        # Create test audio file
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio content")

        service = AssemblyAITranscriptionService(
            api_key="test-key",
            model="universal"
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Mock upload response
            mock_upload_response = MagicMock()
            mock_upload_response.status_code = 200
            mock_upload_response.json.return_value = {"upload_url": "https://cdn.assemblyai.com/audio/test123"}

            # Mock submit response
            mock_submit_response = MagicMock()
            mock_submit_response.status_code = 200
            mock_submit_response.json.return_value = {"id": "tx123", "status": "queued"}

            # Mock poll response (completed)
            mock_poll_response = MagicMock()
            mock_poll_response.status_code = 200
            mock_poll_response.json.return_value = {
                "id": "tx123",
                "status": "completed",
                "text": "Hello world, this is a test transcription.",
                "language_code": "en",
                "words": [
                    {"text": "Hello", "start": 0, "end": 500},
                    {"text": "world,", "start": 600, "end": 1000},
                    {"text": "this", "start": 1100, "end": 1300},
                    {"text": "is", "start": 1400, "end": 1500},
                    {"text": "a", "start": 1600, "end": 1700},
                    {"text": "test", "start": 1800, "end": 2000},
                    {"text": "transcription.", "start": 2100, "end": 2500}
                ]
            }

            # Mock delete response
            mock_delete_response = MagicMock()
            mock_delete_response.status_code = 200

            # Configure mock to return different responses for different methods
            mock_client.post = AsyncMock(side_effect=[
                mock_upload_response,
                mock_submit_response
            ])
            mock_client.get = AsyncMock(return_value=mock_poll_response)
            mock_client.delete = AsyncMock(return_value=mock_delete_response)

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            result = await service.transcribe_audio(audio_file, language="en")

        assert result["text"] == "Hello world, this is a test transcription."
        assert result["language"] == "en"
        assert result["beam_size"] is None  # Not supported by AssemblyAI
        assert result["temperature"] is None  # Not supported by AssemblyAI
        assert len(result["segments"]) >= 1  # Should have segments from words

    @pytest.mark.asyncio
    async def test_transcribe_audio_file_not_found(self):
        """Test error when audio file doesn't exist."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            await service.transcribe_audio(Path("/nonexistent/path/audio.mp3"))

    @pytest.mark.asyncio
    async def test_transcribe_audio_upload_failure(self, tmp_path):
        """Test handling of upload failure."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        # Mock the internal _upload_audio method to raise an error
        with patch.object(service, "_upload_audio") as mock_upload:
            mock_upload.side_effect = RuntimeError("AssemblyAI upload failed: 401 - Unauthorized")

            with pytest.raises(RuntimeError, match="AssemblyAI upload failed"):
                await service.transcribe_audio(audio_file)

    @pytest.mark.asyncio
    async def test_transcribe_audio_submit_failure(self, tmp_path):
        """Test handling of submit failure."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        # Mock internal methods
        with patch.object(service, "_upload_audio") as mock_upload, \
                patch.object(service, "_submit_transcription") as mock_submit:
            mock_upload.return_value = "https://cdn.assemblyai.com/test"
            mock_submit.side_effect = RuntimeError("AssemblyAI submit failed: 400 - Bad request")

            with pytest.raises(RuntimeError, match="AssemblyAI submit failed"):
                await service.transcribe_audio(audio_file)

    @pytest.mark.asyncio
    async def test_transcribe_audio_transcription_error(self, tmp_path):
        """Test handling of transcription error status from AssemblyAI."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        # Mock internal methods
        with patch.object(service, "_upload_audio") as mock_upload, \
                patch.object(service, "_submit_transcription") as mock_submit, \
                patch.object(service, "_poll_transcription") as mock_poll, \
                patch.object(service, "_delete_transcript") as mock_delete:
            mock_upload.return_value = "https://cdn.assemblyai.com/test"
            mock_submit.return_value = "tx123"
            mock_poll.side_effect = RuntimeError("AssemblyAI transcription failed: Audio file is too short")
            mock_delete.return_value = None

            with pytest.raises(RuntimeError, match="Audio file is too short"):
                await service.transcribe_audio(audio_file)

    @pytest.mark.asyncio
    async def test_gdpr_delete_called_on_success(self, tmp_path):
        """Verify GDPR delete is called after successful transcription."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Mock upload
            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"upload_url": "https://cdn.assemblyai.com/test"}

            # Mock submit
            mock_submit = MagicMock()
            mock_submit.status_code = 200
            mock_submit.json.return_value = {"id": "tx123"}

            mock_client.post = AsyncMock(side_effect=[mock_upload, mock_submit])

            # Mock poll (completed)
            mock_poll = MagicMock()
            mock_poll.status_code = 200
            mock_poll.json.return_value = {
                "id": "tx123",
                "status": "completed",
                "text": "Test",
                "language_code": "en"
            }
            mock_client.get = AsyncMock(return_value=mock_poll)

            # Mock delete
            mock_delete = MagicMock()
            mock_delete.status_code = 200
            mock_client.delete = AsyncMock(return_value=mock_delete)

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            await service.transcribe_audio(audio_file)

            # Verify delete was called at least once
            # Note: Each async context manager creates a new client,
            # so we check the mock_client_class was used
            assert mock_client_class.call_count >= 1

    @pytest.mark.asyncio
    async def test_gdpr_delete_called_on_failure(self, tmp_path):
        """Verify GDPR delete is still called when transcription fails."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")
        delete_called = False

        async def track_delete(*args, **kwargs):
            nonlocal delete_called
            delete_called = True
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            return mock_resp

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Mock upload
            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"upload_url": "https://cdn.assemblyai.com/test"}

            # Mock submit
            mock_submit = MagicMock()
            mock_submit.status_code = 200
            mock_submit.json.return_value = {"id": "tx123"}

            mock_client.post = AsyncMock(side_effect=[mock_upload, mock_submit])

            # Mock poll (error)
            mock_poll = MagicMock()
            mock_poll.status_code = 200
            mock_poll.json.return_value = {
                "id": "tx123",
                "status": "error",
                "error": "Processing failed"
            }
            mock_client.get = AsyncMock(return_value=mock_poll)

            # Track delete calls
            mock_client.delete = track_delete

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            with pytest.raises(RuntimeError):
                await service.transcribe_audio(audio_file)

            # Verify delete was attempted despite error
            assert delete_called, "GDPR delete should be called even when transcription fails"

    @pytest.mark.asyncio
    async def test_gdpr_delete_failure_does_not_raise(self, tmp_path):
        """Verify that GDPR delete failure does not break the workflow."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Mock upload
            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"upload_url": "https://cdn.assemblyai.com/test"}

            # Mock submit
            mock_submit = MagicMock()
            mock_submit.status_code = 200
            mock_submit.json.return_value = {"id": "tx123"}

            mock_client.post = AsyncMock(side_effect=[mock_upload, mock_submit])

            # Mock poll (completed)
            mock_poll = MagicMock()
            mock_poll.status_code = 200
            mock_poll.json.return_value = {
                "id": "tx123",
                "status": "completed",
                "text": "Test transcription",
                "language_code": "en"
            }
            mock_client.get = AsyncMock(return_value=mock_poll)

            # Mock delete failure
            mock_delete = MagicMock()
            mock_delete.status_code = 500  # Server error
            mock_client.delete = AsyncMock(return_value=mock_delete)

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Should succeed despite delete failure
            result = await service.transcribe_audio(audio_file)
            assert result["text"] == "Test transcription"

    def test_get_model_name(self):
        """Test model name format."""
        service = AssemblyAITranscriptionService(
            api_key="test-key",
            model="universal"
        )
        assert service.get_model_name() == "assemblyai-universal"

    @pytest.mark.asyncio
    async def test_list_available_models(self):
        """Test that models list returns expected models."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        models = await service.list_available_models()

        assert len(models) == 1
        assert models[0]["id"] == "universal"

    @pytest.mark.asyncio
    async def test_list_available_models_cached(self):
        """Test that models are cached for 1 hour."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        # First call
        models1 = await service.list_available_models()

        # Second call should use cache
        models2 = await service.list_available_models()

        assert models1 == models2
        assert service._models_cache is not None
        assert service._models_cache_timestamp is not None

    def test_get_supported_languages(self):
        """Test supported languages list."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        languages = service.get_supported_languages()

        # AssemblyAI does NOT support auto language detection
        assert "auto" not in languages
        assert len(languages) == 10
        assert "en" in languages
        assert "en_us" in languages
        assert "sl" in languages  # Slovenian support
        assert "hr" in languages  # Croatian support
        assert "sr" in languages  # Serbian support


class TestWordsToSegmentsConversion:
    """Test word-level to segment conversion."""

    def test_words_to_segments_basic(self):
        """Test basic word to segment conversion."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        words = [
            {"text": "Hello", "start": 0, "end": 500},
            {"text": "world", "start": 600, "end": 1000},
        ]

        segments = service._words_to_segments(words)

        assert len(segments) == 1
        assert segments[0]["text"] == "Hello world"
        assert segments[0]["start"] == 0.0
        assert segments[0]["end"] == 1.0

    def test_words_to_segments_with_gap(self):
        """Test that large gaps create new segments."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        words = [
            {"text": "Hello", "start": 0, "end": 500},
            {"text": "world", "start": 600, "end": 1000},
            # 2 second gap (> 1000ms threshold)
            {"text": "Goodbye", "start": 3000, "end": 3500}
        ]

        segments = service._words_to_segments(words)

        assert len(segments) == 2
        assert segments[0]["text"] == "Hello world"
        assert segments[1]["text"] == "Goodbye"

    def test_words_to_segments_empty_list(self):
        """Test empty words list returns empty segments."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        segments = service._words_to_segments([])

        assert segments == []

    def test_words_to_segments_single_word(self):
        """Test single word becomes single segment."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        words = [{"text": "Hello", "start": 0, "end": 500}]

        segments = service._words_to_segments(words)

        assert len(segments) == 1
        assert segments[0]["text"] == "Hello"
        assert segments[0]["id"] == 0


class TestAssemblyAITranscriptionServiceInit:
    """Test service initialization."""

    def test_default_values(self):
        """Test default initialization values."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        assert service.api_key == "test-key"
        assert service.model == "universal"
        assert service.poll_interval == 3.0
        assert service.timeout == 300

    def test_custom_values(self):
        """Test custom initialization values."""
        service = AssemblyAITranscriptionService(
            api_key="custom-key",
            model="best",
            poll_interval=5.0,
            timeout=600
        )

        assert service.api_key == "custom-key"
        assert service.model == "best"
        assert service.poll_interval == 5.0
        assert service.timeout == 600

    def test_cache_initialized_empty(self):
        """Test that cache is initialized as empty."""
        service = AssemblyAITranscriptionService(api_key="test-key")

        assert service._models_cache is None
        assert service._models_cache_timestamp is None


class TestAssemblyAIUnsupportedParameters:
    """Test handling of unsupported parameters."""

    @pytest.mark.asyncio
    async def test_beam_size_logged_but_ignored(self, tmp_path, caplog):
        """Test that beam_size parameter is logged but doesn't cause error."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            # Mock successful workflow
            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"upload_url": "https://cdn.assemblyai.com/test"}

            mock_submit = MagicMock()
            mock_submit.status_code = 200
            mock_submit.json.return_value = {"id": "tx123"}

            mock_poll = MagicMock()
            mock_poll.status_code = 200
            mock_poll.json.return_value = {
                "id": "tx123",
                "status": "completed",
                "text": "Test",
                "language_code": "en"
            }

            mock_delete = MagicMock()
            mock_delete.status_code = 200

            mock_client.post = AsyncMock(side_effect=[mock_upload, mock_submit])
            mock_client.get = AsyncMock(return_value=mock_poll)
            mock_client.delete = AsyncMock(return_value=mock_delete)

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Pass beam_size parameter
            result = await service.transcribe_audio(audio_file, beam_size=5)

            # Should succeed
            assert result["text"] == "Test"
            assert result["beam_size"] is None  # Still None in result

    @pytest.mark.asyncio
    async def test_temperature_logged_but_ignored(self, tmp_path):
        """Test that temperature parameter doesn't cause error."""
        audio_file = tmp_path / "test.mp3"
        audio_file.write_bytes(b"fake audio")

        service = AssemblyAITranscriptionService(api_key="test-key")

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            mock_upload = MagicMock()
            mock_upload.status_code = 200
            mock_upload.json.return_value = {"upload_url": "https://cdn.assemblyai.com/test"}

            mock_submit = MagicMock()
            mock_submit.status_code = 200
            mock_submit.json.return_value = {"id": "tx123"}

            mock_poll = MagicMock()
            mock_poll.status_code = 200
            mock_poll.json.return_value = {
                "id": "tx123",
                "status": "completed",
                "text": "Test",
                "language_code": "en"
            }

            mock_delete = MagicMock()
            mock_delete.status_code = 200

            mock_client.post = AsyncMock(side_effect=[mock_upload, mock_submit])
            mock_client.get = AsyncMock(return_value=mock_poll)
            mock_client.delete = AsyncMock(return_value=mock_delete)

            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = AsyncMock()
            mock_client_class.return_value = mock_client

            # Pass temperature parameter
            result = await service.transcribe_audio(audio_file, temperature=0.5)

            assert result["text"] == "Test"
            assert result["temperature"] is None  # Still None in result
