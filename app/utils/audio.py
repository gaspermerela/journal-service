"""
Audio utilities for calculating audio file metadata.
"""
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from app.utils.logger import get_logger

logger = get_logger("audio_utils")


def get_audio_duration(file_path: str) -> float:
    """
    Calculate audio duration in seconds using mutagen.

    Args:
        file_path: Path to audio file (MP3, M4A, etc.)

    Returns:
        Duration in seconds (float)
        Returns 0.0 if calculation fails
    """
    try:
        # Determine file type and use appropriate mutagen class
        if file_path.lower().endswith('.mp3'):
            audio = MP3(file_path)
        elif file_path.lower().endswith(('.m4a', '.mp4')):
            audio = MP4(file_path)
        else:
            logger.warning(
                f"Unsupported audio format, defaulting to 0.0",
                file_path=file_path
            )
            return 0.0

        duration_seconds = audio.info.length
        logger.info(f"Audio duration calculated", file_path=file_path, duration=duration_seconds)
        return duration_seconds
    except Exception as e:
        logger.warning(
            f"Failed to calculate audio duration, defaulting to 0.0",
            file_path=file_path,
            error=str(e)
        )
        return 0.0
