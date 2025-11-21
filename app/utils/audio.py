"""
Audio utilities for calculating audio file metadata.
"""
from mutagen import File as MutagenFile
from app.utils.logger import get_logger

logger = get_logger("audio_utils")


def get_audio_duration(file_path: str) -> float:
    """
    Calculate audio duration in seconds using mutagen.

    Supports all common audio formats: MP3, M4A, WAV, OGG, AAC, FLAC, WebM, etc.

    Args:
        file_path: Path to audio file

    Returns:
        Duration in seconds (float)
        Returns 0.0 if calculation fails
    """
    try:
        # Use mutagen's File class which auto-detects format
        audio = MutagenFile(file_path)

        if audio is None:
            logger.warning(
                f"Mutagen could not detect audio format",
                file_path=file_path
            )
            return 0.0

        if audio.info is None or not hasattr(audio.info, 'length'):
            logger.warning(
                f"Audio file has no duration info",
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
