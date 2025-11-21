"""
Unit tests for transcription service.
Tests WhisperLocalService with mocked Whisper model.
"""
import pytest
from pathlib import Path
from unittest.mock import patch

from app.services.transcription import WhisperLocalService


@pytest.mark.asyncio
async def test_transcribe_audio_success(mock_whisper_model, tmp_path):
    """Test successful audio transcription with mocked Whisper model."""
    # Create a fake audio file
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Create service with mocked model
    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu", num_threads=4)

    # Transcribe
    result = await service.transcribe_audio(audio_file, language="en")

    # Verify result
    assert result["text"] == "I had a dream about flying over mountains and vast oceans."
    assert result["language"] == "en"
    assert len(result["segments"]) == 2
    assert result["segments"][0]["text"] == "I had a dream about flying"

    # Verify model was called correctly
    mock_whisper_model.transcribe.assert_called_once()
    call_args = mock_whisper_model.transcribe.call_args
    assert str(audio_file) in call_args[0]


@pytest.mark.asyncio
async def test_transcribe_audio_auto_language(mock_whisper_model, tmp_path):
    """Test transcription with automatic language detection."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    result = await service.transcribe_audio(audio_file, language="auto")

    # Verify auto language was passed as None to Whisper
    call_kwargs = mock_whisper_model.transcribe.call_args[1]
    assert call_kwargs["language"] is None


@pytest.mark.asyncio
async def test_transcribe_audio_file_not_found(mock_whisper_model, tmp_path):
    """Test transcription fails when audio file doesn't exist."""
    non_existent_file = tmp_path / "does_not_exist.mp3"

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    with pytest.raises(FileNotFoundError) as exc_info:
        await service.transcribe_audio(non_existent_file, language="en")

    assert "Audio file not found" in str(exc_info.value)
    mock_whisper_model.transcribe.assert_not_called()


@pytest.mark.asyncio
async def test_transcribe_audio_model_error(mock_whisper_model, tmp_path):
    """Test transcription handles Whisper model errors gracefully."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Make model raise an error
    mock_whisper_model.transcribe.side_effect = RuntimeError("Model error")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    with pytest.raises(RuntimeError) as exc_info:
        await service.transcribe_audio(audio_file, language="en")

    assert "Transcription failed" in str(exc_info.value)
    assert "Model error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_transcribe_audio_with_different_languages(mock_whisper_model, tmp_path):
    """Test transcription with various language codes."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    languages = ["en", "es", "fr", "de", "auto"]

    for lang in languages:
        mock_whisper_model.reset_mock()
        result = await service.transcribe_audio(audio_file, language=lang)

        assert "text" in result
        assert "language" in result
        mock_whisper_model.transcribe.assert_called_once()


def test_get_supported_languages(mock_whisper_model):
    """Test getting list of supported languages."""
    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    languages = service.get_supported_languages()

    assert isinstance(languages, list)
    assert len(languages) > 50  # Whisper supports 99+ languages
    assert "en" in languages
    assert "es" in languages
    assert "auto" in languages


def test_service_initialization_cpu(mock_whisper_model):
    """Test service initializes correctly with CPU device."""
    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu", num_threads=8)

    assert service.model == mock_whisper_model
    assert service.device == "cpu"
    assert service.num_threads == 8


def test_service_initialization_cuda(mock_whisper_model):
    """Test service initializes correctly with CUDA device."""
    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cuda", num_threads=4)

    assert service.model == mock_whisper_model
    assert service.device == "cuda"


@pytest.mark.asyncio
async def test_transcribe_strips_whitespace(mock_whisper_model, tmp_path):
    """Test that transcribed text is properly stripped of whitespace."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Mock model returns text with extra whitespace
    mock_whisper_model.transcribe.return_value = {
        "text": "  Text with whitespace  \n",
        "language": "en",
        "segments": []
    }

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")
    result = await service.transcribe_audio(audio_file, language="en")

    assert result["text"] == "Text with whitespace"
    assert not result["text"].startswith(" ")
    assert not result["text"].endswith(" ")


@pytest.mark.asyncio
async def test_transcription_options_configured_correctly(mock_whisper_model, tmp_path):
    """Test that transcription is called with correct options."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")
    await service.transcribe_audio(audio_file, language="en")

    call_kwargs = mock_whisper_model.transcribe.call_args[1]

    # Verify transcription options
    assert call_kwargs["fp16"] is False  # Required for CPU
    assert call_kwargs["language"] == "en"
    assert call_kwargs["task"] == "transcribe"
    assert call_kwargs["beam_size"] == 5  # Config default (WHISPER_DEFAULT_BEAM_SIZE)
    assert call_kwargs["best_of"] == 1


@pytest.mark.asyncio
async def test_transcribe_async_execution(mock_whisper_model, tmp_path):
    """Test that transcription runs asynchronously without blocking."""
    import asyncio

    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")

    # Run transcription and another task concurrently
    async def other_task():
        await asyncio.sleep(0.01)
        return "completed"

    result, other = await asyncio.gather(
        service.transcribe_audio(audio_file, language="en"),
        other_task()
    )

    assert result["text"] is not None
    assert other == "completed"


@pytest.mark.asyncio
async def test_transcribe_with_custom_beam_size(mock_whisper_model, tmp_path):
    """Test transcription with custom beam_size parameter."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="base", device="cpu")
    result = await service.transcribe_audio(audio_file, language="en", beam_size=5)

    # Verify beam_size was passed to Whisper
    call_kwargs = mock_whisper_model.transcribe.call_args[1]
    assert call_kwargs["beam_size"] == 5

    # Verify beam_size is in result
    assert result["beam_size"] == 5


@pytest.mark.asyncio
async def test_transcribe_with_default_beam_size(mock_whisper_model, tmp_path):
    """Test transcription uses config default when beam_size not provided."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    service = WhisperLocalService(model=mock_whisper_model, model_name="large-v3", device="cpu")

    # Don't provide beam_size - should use config default
    result = await service.transcribe_audio(audio_file, language="en")

    # Verify default beam_size was used
    call_kwargs = mock_whisper_model.transcribe.call_args[1]
    assert call_kwargs["beam_size"] == 5  # Config default

    # Verify beam_size is in result
    assert result["beam_size"] == 5


@pytest.mark.asyncio
async def test_transcribe_beam_size_overrides_model_default(mock_whisper_model, tmp_path):
    """Test that explicit beam_size overrides model-based default."""
    audio_file = tmp_path / "test_audio.mp3"
    audio_file.write_bytes(b"fake audio data")

    # Use large model (normally uses beam_size=5) but explicitly set to 1
    service = WhisperLocalService(model=mock_whisper_model, model_name="large-v3", device="cpu")
    result = await service.transcribe_audio(audio_file, language="en", beam_size=1)

    # Verify explicit beam_size=1 was used
    call_kwargs = mock_whisper_model.transcribe.call_args[1]
    assert call_kwargs["beam_size"] == 1
    assert result["beam_size"] == 1
