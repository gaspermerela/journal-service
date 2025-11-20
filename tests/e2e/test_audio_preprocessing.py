"""
E2E tests for audio preprocessing service.

Tests the actual ffmpeg pipeline with real audio files from test fixtures.
Requires ffmpeg to be installed on the system.
"""
import os
import shutil
import wave
from pathlib import Path

import pytest

from app.services.audio_preprocessing import AudioPreprocessingService


# Path to test fixtures
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"
TEST_MP3_FILE = FIXTURES_DIR / "crocodile.mp3"


@pytest.fixture
def preprocessing_service():
    """Create preprocessing service instance."""
    return AudioPreprocessingService()


@pytest.fixture
def test_audio_file(tmp_path):
    """
    Copy the test MP3 file to a temporary directory.

    This allows tests to modify/delete it without affecting the fixture.
    """
    if not TEST_MP3_FILE.exists():
        pytest.skip(f"Test fixture not found: {TEST_MP3_FILE}")

    # Copy to temp directory
    temp_file = tmp_path / "test_input.mp3"
    shutil.copy(TEST_MP3_FILE, temp_file)

    return temp_file


def get_wav_info(file_path: str) -> dict:
    """
    Extract WAV file metadata.

    Returns:
        dict with sample_rate, channels, sample_width, duration
    """
    with wave.open(file_path, 'rb') as wav_file:
        return {
            "sample_rate": wav_file.getframerate(),
            "channels": wav_file.getnchannels(),
            "sample_width": wav_file.getsampwidth(),
            "num_frames": wav_file.getnframes(),
            "duration": wav_file.getnframes() / wav_file.getframerate(),
        }


class TestAudioPreprocessingE2E:
    """E2E tests for audio preprocessing with real ffmpeg."""

    @pytest.mark.asyncio
    async def test_preprocess_audio_converts_to_16khz_mono(
        self, preprocessing_service, test_audio_file
    ):
        """Test that preprocessing converts MP3 to 16kHz mono WAV."""
        # Verify input is MP3
        assert test_audio_file.suffix == ".mp3", "Input should be MP3"

        # Preprocess
        success, output_path, error = await preprocessing_service.preprocess_audio(
            str(test_audio_file)
        )

        # Verify success
        assert success is True
        assert error is None
        assert os.path.exists(output_path)

        # Verify output is 16kHz mono WAV
        assert Path(output_path).suffix == ".wav", "Output should be WAV"
        output_info = get_wav_info(output_path)
        assert output_info["sample_rate"] == 16000, "Should be resampled to 16kHz"
        assert output_info["channels"] == 1, "Should be converted to mono"
        assert output_info["sample_width"] == 2, "Should be 16-bit"

        # Verify duration is non-zero and reasonable
        # Note: silence removal may significantly reduce duration if input has long pauses
        assert output_info["duration"] > 10, "Should have non-zero duration"
        assert output_info["duration"] < 60, "Duration should be less than 1 minute"

    @pytest.mark.asyncio
    async def test_preprocess_audio_replaces_original(
        self, preprocessing_service, test_audio_file
    ):
        """Test that preprocessing replaces the original MP3 with WAV."""
        original_path = str(test_audio_file)
        assert test_audio_file.suffix == ".mp3", "Input should be MP3"

        # Preprocess (no custom output path, should replace)
        success, output_path, error = await preprocessing_service.preprocess_audio(
            original_path
        )

        assert success is True
        assert error is None

        # Original MP3 should be deleted
        assert not os.path.exists(original_path), "Original MP3 should be deleted"

        # Output should be WAV with same base name
        assert Path(output_path).suffix == ".wav", "Output should be WAV"
        assert os.path.exists(output_path), "Preprocessed WAV should exist"
        assert Path(output_path).stem == test_audio_file.stem, "Should have same base name"

    @pytest.mark.asyncio
    async def test_preprocess_audio_with_custom_output_path(
        self, preprocessing_service, test_audio_file, tmp_path
    ):
        """Test preprocessing with custom output path."""
        custom_output = tmp_path / "custom_output.wav"

        success, output_path, error = await preprocessing_service.preprocess_audio(
            str(test_audio_file), str(custom_output)
        )

        assert success is True
        assert error is None
        assert output_path == str(custom_output)
        assert os.path.exists(str(custom_output))

        # Verify it's 16kHz mono
        output_info = get_wav_info(str(custom_output))
        assert output_info["sample_rate"] == 16000
        assert output_info["channels"] == 1

    @pytest.mark.asyncio
    async def test_preprocess_audio_creates_valid_wav(
        self, preprocessing_service, test_audio_file
    ):
        """Test that preprocessed audio is a valid WAV file that can be read."""
        success, output_path, error = await preprocessing_service.preprocess_audio(
            str(test_audio_file)
        )

        assert success is True
        assert error is None

        # Verify we can read it with wave module
        try:
            with wave.open(output_path, 'rb') as wav_file:
                # Read some frames to ensure it's valid
                frames = wav_file.readframes(100)
                assert len(frames) > 0, "Should be able to read audio frames"
        except Exception as e:
            pytest.fail(f"Failed to read preprocessed WAV file: {e}")

    @pytest.mark.asyncio
    async def test_preprocess_audio_handles_missing_file(self, preprocessing_service):
        """Test error handling when input file doesn't exist."""
        nonexistent_file = "/tmp/nonexistent_audio_file_12345.wav"

        success, output_path, error = await preprocessing_service.preprocess_audio(
            nonexistent_file
        )

        # Should fail gracefully
        assert success is False
        assert error is not None
        assert "ffmpeg error" in error or "Preprocessing error" in error

    @pytest.mark.asyncio
    async def test_preprocessing_service_with_different_sample_rate(self, test_audio_file):
        """Test preprocessing with custom sample rate."""
        custom_service = AudioPreprocessingService(sample_rate=8000)

        success, output_path, error = await custom_service.preprocess_audio(
            str(test_audio_file)
        )

        assert success is True

        output_info = get_wav_info(output_path)
        assert output_info["sample_rate"] == 8000, "Should use custom sample rate"
        assert output_info["channels"] == 1

    @pytest.mark.skip(reason="Manual test - unskip to inspect preprocessed audio file")
    @pytest.mark.asyncio
    async def test_manual_inspect_preprocessed_file(self, preprocessing_service):
        """
        Manual inspection test - saves preprocessed file for listening.

        To use this test:
        1. Unskip by commenting out the @pytest.mark.skip decorator
        2. Run: pytest tests/e2e/test_audio_preprocessing.py::TestAudioPreprocessingE2E::test_manual_inspect_preprocessed_file -v -s
        3. The preprocessed file will be saved to /tmp/preprocessed_crocodile.wav
        4. Listen to it to verify quality
        5. Compare with original: /tmp/original_crocodile.mp3
        """
        import shutil

        # Copy original to /tmp for comparison
        original_output = "/tmp/original_crocodile.mp3"
        preprocessed_output = "/tmp/preprocessed_crocodile.wav"

        shutil.copy(TEST_MP3_FILE, original_output)
        print(f"\n✓ Original file copied to: {original_output}")

        # Preprocess
        success, output_path, error = await preprocessing_service.preprocess_audio(
            original_output,
            preprocessed_output
        )

        assert success is True, f"Preprocessing failed: {error}"

        # Print info
        output_info = get_wav_info(preprocessed_output)
        print(f"\n✓ Preprocessed file saved to: {preprocessed_output}")
        print(f"\nAudio Info:")
        print(f"  Sample Rate: {output_info['sample_rate']} Hz")
        print(f"  Channels: {output_info['channels']}")
        print(f"  Duration: {output_info['duration']:.2f} seconds")
        print(f"  Sample Width: {output_info['sample_width']} bytes ({output_info['sample_width'] * 8}-bit)")
        print(f"\nTo listen:")
        print(f"  Original:     afplay {original_output}")
        print(f"  Preprocessed: afplay {preprocessed_output}")
        print(f"\nTo visualize:")
        print(f"  ffplay -showmode 1 {preprocessed_output}")

        # Keep the test passing so output is visible
        assert os.path.exists(preprocessed_output)
        assert output_info["duration"] > 10
