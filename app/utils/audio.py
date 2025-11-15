"""
Audio utilities for calculating audio file metadata.
"""
from pydub import AudioSegment
from app.utils.logger import get_logger

logger = get_logger("audio_utils")


def get_audio_duration(file_path: str) -> float:
    """
    Calculate audio duration in seconds using pydub.

    Args:
        file_path: Path to audio file (MP3, M4A, etc.)

    Returns:
        Duration in seconds (float)
        Returns 0.0 if calculation fails
    """
    try:
        audio = AudioSegment.from_file(file_path)
        duration_seconds = len(audio) / 1000.0  # pydub returns milliseconds
        logger.info(f"Audio duration calculated", file_path=file_path, duration=duration_seconds)
        return duration_seconds
    except Exception as e:
        logger.warning(
            f"Failed to calculate audio duration, defaulting to 0.0",
            file_path=file_path,
            error=str(e)
        )
        return 0.0
