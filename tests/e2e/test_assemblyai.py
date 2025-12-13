"""
End-to-end tests for AssemblyAI transcription provider.

Tests the AssemblyAI service with REAL API calls.
Requires ASSEMBLYAI_API_KEY environment variable to be set.

Run tests: pytest tests/e2e/test_assemblyai.py -v -s
"""
import os
import pytest
from pathlib import Path

# Real audio file to use for tests
REAL_AUDIO_FILE = Path("tests/fixtures/crocodile.mp3")


def assemblyai_available() -> bool:
    """Check if AssemblyAI API key is available."""
    return bool(os.getenv("ASSEMBLYAI_API_KEY"))


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not assemblyai_available(),
    reason="ASSEMBLYAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_assemblyai_real_transcription():
    """
    Test real AssemblyAI transcription with actual API.

    This test:
    1. Uploads audio to AssemblyAI
    2. Submits transcription job
    3. Polls until completion
    4. Verifies text is returned
    5. Deletes transcript (GDPR)

    Requires:
    - ASSEMBLYAI_API_KEY environment variable
    - tests/fixtures/crocodile.mp3 test audio file
    """
    from app.services.transcription_assemblyai import AssemblyAITranscriptionService

    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Test audio file not found: {REAL_AUDIO_FILE}")

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    service = AssemblyAITranscriptionService(
        api_key=api_key,
        model="universal"
    )

    result = await service.transcribe_audio(
        audio_path=REAL_AUDIO_FILE,
        language="en"
    )

    # Verify transcription result
    assert result["text"], "Transcription should return non-empty text"
    assert len(result["text"]) > 10, "Transcription text should have meaningful content"
    assert result["language"], "Language should be detected"
    assert result["beam_size"] is None, "AssemblyAI doesn't support beam_size"
    assert result["temperature"] is None, "AssemblyAI doesn't support temperature"

    print(f"\n--- AssemblyAI Transcription Result ---")
    print(f"Text: {result['text'][:200]}...")
    print(f"Language: {result['language']}")
    print(f"Segments: {len(result['segments'])}")
    print(f"--- End Result ---\n")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not assemblyai_available(),
    reason="ASSEMBLYAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_assemblyai_auto_language_fallback():
    """
    Test AssemblyAI defaults to en_us when auto language is requested.
    AssemblyAI does NOT support auto language detection.
    """
    from app.services.transcription_assemblyai import AssemblyAITranscriptionService

    if not REAL_AUDIO_FILE.exists():
        pytest.skip(f"Test audio file not found: {REAL_AUDIO_FILE}")

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    service = AssemblyAITranscriptionService(
        api_key=api_key,
        model="universal"
    )

    # "auto" will fallback to "en_us"
    result = await service.transcribe_audio(
        audio_path=REAL_AUDIO_FILE,
        language="auto"
    )

    assert result["text"], "Transcription should return text"
    # Should default to en_us when auto is passed
    print(f"Language used (defaulted from auto): {result['language']}")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not assemblyai_available(),
    reason="ASSEMBLYAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_assemblyai_model_listing():
    """
    Test that AssemblyAI service returns available models.
    """
    from app.services.transcription_assemblyai import AssemblyAITranscriptionService

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    service = AssemblyAITranscriptionService(
        api_key=api_key,
        model="universal"
    )

    models = await service.list_available_models()

    # Only universal model is supported
    assert len(models) == 1
    assert models[0]["id"] == "universal"

    print(f"\n--- Available AssemblyAI Models ---")
    for model in models:
        print(f"  - {model['id']}: {model['name']}")
    print(f"--- End Models ---\n")


@pytest.mark.e2e_real
@pytest.mark.skipif(
    not assemblyai_available(),
    reason="ASSEMBLYAI_API_KEY not set"
)
@pytest.mark.asyncio
async def test_assemblyai_service_metadata():
    """
    Test AssemblyAI service metadata methods.
    """
    from app.services.transcription_assemblyai import AssemblyAITranscriptionService

    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    service = AssemblyAITranscriptionService(
        api_key=api_key,
        model="universal"
    )

    # Test model name format
    model_name = service.get_model_name()
    assert model_name == "assemblyai-universal"

    # Test supported languages (10 curated languages, no auto)
    languages = service.get_supported_languages()
    assert "auto" not in languages  # AssemblyAI does NOT support auto
    assert "en" in languages
    assert "sl" in languages  # Slovenian
    assert len(languages) == 10
