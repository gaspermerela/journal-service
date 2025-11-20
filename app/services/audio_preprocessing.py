"""
Audio preprocessing service for optimizing audio files before transcription.

Based on audio_preprocessing_guide.md, this service applies a standardized
ffmpeg pipeline to ALL audio files:
1. Convert to mono WAV
2. Resample to 16kHz (optimal for Whisper)
3. Apply high-pass filter (60Hz)
4. Normalize loudness (EBU R128)
5. Remove silence (start and end)

This ensures consistent audio quality for transcription regardless of input format.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("audio_preprocessing")


class AudioPreprocessingService:
    """
    Service for preprocessing audio files before transcription.

    Applies a standardized 5-step pipeline to ALL audio files:
    1. Convert to WAV mono 16kHz
    2. High-pass filter (60Hz)
    3. Loudness normalization (EBU R128)
    4. Silence removal
    5. Output preprocessed WAV
    """

    def __init__(
        self,
        sample_rate: int = 16000,
        highpass_freq: int = 60,
        loudnorm_i: int = -16,
        loudnorm_tp: float = -1.5,
        loudnorm_lra: int = 11,
        silence_threshold: str = "-80dB",
        silence_duration: float = 0.5,
    ):
        """
        Initialize preprocessing service with configurable parameters.

        Args:
            sample_rate: Target sample rate (16kHz recommended for Whisper)
            highpass_freq: High-pass filter frequency in Hz
            loudnorm_i: Integrated loudness target (LUFS)
            loudnorm_tp: True peak target (dBTP)
            loudnorm_lra: Loudness range target (LU)
            silence_threshold: Silence threshold in dB
            silence_duration: Minimum silence duration in seconds
        """
        self.sample_rate = sample_rate
        self.highpass_freq = highpass_freq
        self.loudnorm_i = loudnorm_i
        self.loudnorm_tp = loudnorm_tp
        self.loudnorm_lra = loudnorm_lra
        self.silence_threshold = silence_threshold
        self.silence_duration = silence_duration

    def _build_ffmpeg_command(self, input_path: str, output_path: str) -> list[str]:
        """
        Build ffmpeg command with full preprocessing pipeline.

        Pipeline (from audio_preprocessing_guide.md):
        1. Convert to mono (-ac 1)
        2. Resample to 16kHz (-ar 16000)
        3. High-pass filter (60Hz)
        4. Loudness normalization (EBU R128)
        5. Silence removal (start and end)

        Args:
            input_path: Input audio file path
            output_path: Output WAV file path

        Returns:
            List of command arguments for subprocess
        """
        # Build audio filter chain
        filters = [
            f"highpass=f={self.highpass_freq}",
            f"loudnorm=I={self.loudnorm_i}:TP={self.loudnorm_tp}:LRA={self.loudnorm_lra}",
            (
                f"silenceremove="
                f"start_periods=1:start_silence={self.silence_duration}:start_threshold={self.silence_threshold}:"
                f"stop_periods=1:stop_silence={self.silence_duration}:stop_threshold={self.silence_threshold}"
            ),
        ]

        audio_filter = ",".join(filters)

        return [
            "ffmpeg",
            "-i", input_path,           # Input file
            "-ac", "1",                 # Mono
            "-ar", str(self.sample_rate),  # 16kHz
            "-af", audio_filter,        # Apply filter chain
            "-y",                       # Overwrite output
            output_path,                # Output WAV file
        ]

    async def preprocess_audio(
        self,
        input_path: str,
        output_path: Optional[str] = None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Preprocess audio file using ffmpeg pipeline.

        Always applies the full preprocessing pipeline to ensure consistent
        audio quality regardless of input format.

        Args:
            input_path: Path to input audio file
            output_path: Path for output file (default: replaces input with .wav)

        Returns:
            Tuple of (success, output_path, error_message)
            - success: True if preprocessing succeeded
            - output_path: Path to processed file
            - error_message: Error description if success=False, None otherwise
        """
        try:
            # Determine output path
            if output_path is None:
                # Replace original: change extension to .wav
                output_path = str(Path(input_path).with_suffix(".wav"))

            # If input and output paths are the same, use temp file
            # (ffmpeg cannot edit files in-place)
            use_temp = (input_path == output_path)
            if use_temp:
                temp_output = str(Path(input_path).with_suffix(".preprocessed.wav"))
            else:
                temp_output = output_path

            logger.info(
                "Starting audio preprocessing",
                input_path=input_path,
                output_path=output_path,
                temp_output=temp_output if use_temp else None,
                sample_rate=self.sample_rate,
            )

            # Build and execute ffmpeg command
            cmd = self._build_ffmpeg_command(input_path, temp_output)

            # Run ffmpeg in subprocess (CPU-bound operation)
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_msg = stderr.decode("utf-8", errors="replace")
                logger.error(
                    "ffmpeg preprocessing failed",
                    input_path=input_path,
                    return_code=process.returncode,
                    error=error_msg,
                )
                # Clean up temp file if it was created
                if use_temp and os.path.exists(temp_output):
                    os.remove(temp_output)
                return False, input_path, f"ffmpeg error: {error_msg}"

            # Verify temp output file exists
            if not os.path.exists(temp_output):
                logger.error(
                    "Preprocessed file not created",
                    output_path=temp_output,
                )
                return False, input_path, "Output file was not created"

            # If we used a temp file, replace the original
            if use_temp:
                try:
                    os.remove(input_path)  # Delete original
                    os.rename(temp_output, output_path)  # Rename temp to final
                    logger.info(
                        "Replaced original file with preprocessed version",
                        path=output_path,
                    )
                except OSError as e:
                    logger.error(
                        "Failed to replace original file",
                        input_path=input_path,
                        temp_output=temp_output,
                        error=str(e),
                    )
                    return False, input_path, f"Failed to replace file: {str(e)}"

            # If preprocessing changed the file extension (non-temp case), delete the original
            elif output_path != input_path and os.path.exists(output_path):
                try:
                    os.remove(input_path)
                    logger.info(
                        "Deleted original file after preprocessing",
                        deleted_path=input_path,
                    )
                except OSError as e:
                    logger.warning(
                        "Failed to delete original file",
                        path=input_path,
                        error=str(e),
                    )

            logger.info(
                "Audio preprocessing completed successfully",
                output_path=output_path,
            )

            return True, output_path, None

        except Exception as e:
            logger.error(
                "Unexpected error during preprocessing",
                input_path=input_path,
                error=str(e),
                exc_info=True,
            )
            return False, input_path, f"Preprocessing error: {str(e)}"


# Global service instance (initialized with config from environment)
preprocessing_service = AudioPreprocessingService(
    sample_rate=settings.PREPROCESSING_SAMPLE_RATE,
    highpass_freq=settings.PREPROCESSING_HIGHPASS_FREQ,
    loudnorm_i=settings.PREPROCESSING_LOUDNORM_I,
    loudnorm_tp=settings.PREPROCESSING_LOUDNORM_TP,
    loudnorm_lra=settings.PREPROCESSING_LOUDNORM_LRA,
    silence_threshold=settings.PREPROCESSING_SILENCE_THRESHOLD,
    silence_duration=settings.PREPROCESSING_SILENCE_DURATION,
)
