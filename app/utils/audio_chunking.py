"""
Audio chunking utilities for splitting long audio files.
Used by RunPod transcription service to handle 1h+ recordings.

Uses mutagen for duration detection and ffmpeg for chunking (no pydub dependency).
"""
import asyncio
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from mutagen import File as MutagenFile

from app.utils.logger import get_logger

logger = get_logger("audio_chunking")


@dataclass
class AudioChunk:
    """Represents a chunk of audio for processing."""
    index: int
    path: Path
    start_time_ms: int
    end_time_ms: int
    duration_ms: int


class AudioChunker:
    """
    Handles audio chunking for long audio files.

    Splits long audio files into smaller chunks suitable for transcription
    services with duration limits. Uses ffmpeg for reliable audio processing.
    """

    def __init__(
        self,
        chunk_duration_seconds: int = 240,
        overlap_seconds: int = 5,
        min_silence_len_ms: int = 800,
        silence_thresh_db: int = -40,
        silence_search_window_ms: int = 30000
    ):
        """
        Initialize audio chunker.

        Args:
            chunk_duration_seconds: Target duration for each chunk (default: 4 min)
            overlap_seconds: Overlap between chunks to avoid cutting words (default: 5s)
            min_silence_len_ms: Minimum silence length to consider for splitting (default: 800ms)
            silence_thresh_db: Silence threshold in dB (default: -40dB)
            silence_search_window_ms: Window to search for silence at chunk boundaries (default: 30s)
        """
        self.chunk_duration_seconds = chunk_duration_seconds
        self.overlap_seconds = overlap_seconds
        self.min_silence_len_ms = min_silence_len_ms
        self.silence_thresh_db = silence_thresh_db
        self.silence_search_window_ms = silence_search_window_ms

        self._temp_dir: Optional[Path] = None

    def _get_duration_ms(self, audio_path: Path) -> int:
        """
        Get audio duration in milliseconds using mutagen.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in milliseconds
        """
        audio = MutagenFile(str(audio_path))
        if audio is None or audio.info is None:
            raise ValueError(f"Could not read audio file: {audio_path}")
        return int(audio.info.length * 1000)

    def needs_chunking(self, audio_path: Path, threshold_seconds: int = 300) -> bool:
        """
        Check if audio file exceeds duration threshold and needs chunking.

        Args:
            audio_path: Path to audio file
            threshold_seconds: Duration threshold in seconds (default: 5 min)

        Returns:
            True if audio duration exceeds threshold
        """
        try:
            duration_ms = self._get_duration_ms(audio_path)
            duration_seconds = duration_ms / 1000
            needs_chunk = duration_seconds > threshold_seconds

            logger.info(
                "Checked if audio needs chunking",
                audio_path=str(audio_path),
                duration_seconds=duration_seconds,
                threshold_seconds=threshold_seconds,
                needs_chunking=needs_chunk
            )
            return needs_chunk
        except Exception as e:
            logger.error(
                "Failed to check audio duration",
                audio_path=str(audio_path),
                error=str(e)
            )
            raise

    def _extract_chunk_ffmpeg(
        self,
        audio_path: Path,
        output_path: Path,
        start_ms: int,
        end_ms: int
    ) -> None:
        """
        Extract a chunk from audio file using ffmpeg.

        Args:
            audio_path: Source audio file
            output_path: Output chunk file path
            start_ms: Start time in milliseconds
            end_ms: End time in milliseconds
        """
        start_seconds = start_ms / 1000
        duration_seconds = (end_ms - start_ms) / 1000

        cmd = [
            "ffmpeg",
            "-i", str(audio_path),
            "-ss", str(start_seconds),
            "-t", str(duration_seconds),
            "-ac", "1",           # Mono
            "-ar", "16000",       # 16kHz
            "-y",                 # Overwrite
            str(output_path)
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {result.stderr}")

    def chunk_audio(
        self,
        audio_path: Path,
        output_dir: Optional[Path] = None,
        use_silence_detection: bool = True
    ) -> List[AudioChunk]:
        """
        Split audio file into chunks.

        Args:
            audio_path: Path to input audio file (WAV recommended)
            output_dir: Directory for chunk files (uses temp dir if None)
            use_silence_detection: Whether to use silence detection for boundaries
                                   (currently ignored, uses fixed boundaries)

        Returns:
            List of AudioChunk objects with paths to chunk files
        """
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Get audio duration
        logger.info("Loading audio for chunking", audio_path=str(audio_path))
        duration_ms = self._get_duration_ms(audio_path)

        chunk_duration_ms = self.chunk_duration_seconds * 1000
        overlap_ms = self.overlap_seconds * 1000

        # Set up output directory
        if output_dir is None:
            self._temp_dir = Path(tempfile.mkdtemp(prefix="audio_chunks_"))
            output_dir = self._temp_dir
        else:
            output_dir.mkdir(parents=True, exist_ok=True)

        # If audio is short enough, return single chunk (just reference original)
        if duration_ms <= chunk_duration_ms:
            logger.info(
                "Audio short enough, no chunking needed",
                duration_ms=duration_ms,
                chunk_threshold_ms=chunk_duration_ms
            )
            return [AudioChunk(
                index=0,
                path=audio_path,
                start_time_ms=0,
                end_time_ms=duration_ms,
                duration_ms=duration_ms
            )]

        chunks = []
        chunk_index = 0
        position = 0

        while position < duration_ms:
            # Calculate chunk end
            chunk_end = min(position + chunk_duration_ms, duration_ms)

            # Export chunk using ffmpeg
            chunk_filename = f"chunk_{chunk_index:04d}.wav"
            chunk_path = output_dir / chunk_filename

            self._extract_chunk_ffmpeg(audio_path, chunk_path, position, chunk_end)

            chunks.append(AudioChunk(
                index=chunk_index,
                path=chunk_path,
                start_time_ms=position,
                end_time_ms=chunk_end,
                duration_ms=chunk_end - position
            ))

            logger.debug(
                "Created chunk",
                chunk_index=chunk_index,
                start_ms=position,
                end_ms=chunk_end,
                duration_ms=chunk_end - position
            )

            # If we've reached the end of audio, we're done
            if chunk_end >= duration_ms:
                break

            # Move position, accounting for overlap to avoid cutting words
            position = chunk_end - overlap_ms
            chunk_index += 1

        logger.info(
            "Audio chunking complete",
            audio_path=str(audio_path),
            total_duration_ms=duration_ms,
            num_chunks=len(chunks),
            chunk_duration_target_s=self.chunk_duration_seconds,
            overlap_s=self.overlap_seconds
        )

        return chunks

    def cleanup_chunks(self, chunks: List[AudioChunk]) -> None:
        """
        Delete temporary chunk files.

        Args:
            chunks: List of AudioChunk objects to clean up
        """
        cleaned = 0
        for chunk in chunks:
            try:
                # Don't delete the original file (index 0 when no chunking)
                if chunk.path.exists() and "chunk_" in chunk.path.name:
                    chunk.path.unlink()
                    cleaned += 1
            except Exception as e:
                logger.warning(
                    "Failed to delete chunk file",
                    chunk_path=str(chunk.path),
                    error=str(e)
                )

        # Clean up temp directory if we created one
        if self._temp_dir and self._temp_dir.exists():
            try:
                self._temp_dir.rmdir()
            except Exception:
                pass  # Directory not empty or other issue

        logger.info("Cleaned up chunk files", cleaned_count=cleaned)

    def get_chunk_metadata(self, chunks: List[AudioChunk]) -> dict:
        """
        Get metadata about chunking for logging/debugging.

        Args:
            chunks: List of AudioChunk objects

        Returns:
            Dict with chunking statistics
        """
        if not chunks:
            return {"num_chunks": 0, "total_duration_ms": 0}

        total_duration_ms = sum(c.duration_ms for c in chunks)
        avg_duration_ms = total_duration_ms / len(chunks)

        return {
            "num_chunks": len(chunks),
            "total_duration_ms": total_duration_ms,
            "avg_chunk_duration_ms": avg_duration_ms,
            "min_chunk_duration_ms": min(c.duration_ms for c in chunks),
            "max_chunk_duration_ms": max(c.duration_ms for c in chunks),
        }
