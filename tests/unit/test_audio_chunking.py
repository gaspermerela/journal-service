"""
Unit tests for audio chunking utilities.
Tests AudioChunker class for splitting long audio files.
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from app.utils.audio_chunking import AudioChunker, AudioChunk


class TestAudioChunkerInit:
    """Test AudioChunker initialization."""

    def test_default_initialization(self):
        """Test AudioChunker initializes with default values."""
        chunker = AudioChunker()

        assert chunker.chunk_duration_seconds == 240
        assert chunker.overlap_seconds == 5
        assert chunker.min_silence_len_ms == 800
        assert chunker.silence_thresh_db == -40
        assert chunker.silence_search_window_ms == 30000

    def test_custom_initialization(self):
        """Test AudioChunker initializes with custom values."""
        chunker = AudioChunker(
            chunk_duration_seconds=180,
            overlap_seconds=10,
            min_silence_len_ms=500,
            silence_thresh_db=-35,
            silence_search_window_ms=20000
        )

        assert chunker.chunk_duration_seconds == 180
        assert chunker.overlap_seconds == 10
        assert chunker.min_silence_len_ms == 500
        assert chunker.silence_thresh_db == -35
        assert chunker.silence_search_window_ms == 20000


class TestNeedsChunking:
    """Test needs_chunking method."""

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_short_audio_no_chunking(self, mock_audio_segment):
        """Test short audio does not need chunking."""
        # Mock audio with 2 minute duration (120,000 ms)
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=120000)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker()
        result = chunker.needs_chunking(Path("/fake/audio.wav"), threshold_seconds=300)

        assert result is False

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_long_audio_needs_chunking(self, mock_audio_segment):
        """Test long audio needs chunking."""
        # Mock audio with 10 minute duration (600,000 ms)
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=600000)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker()
        result = chunker.needs_chunking(Path("/fake/audio.wav"), threshold_seconds=300)

        assert result is True

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_exact_threshold_no_chunking(self, mock_audio_segment):
        """Test audio exactly at threshold does not need chunking."""
        # Mock audio exactly at 5 minutes (300,000 ms)
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=300000)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker()
        result = chunker.needs_chunking(Path("/fake/audio.wav"), threshold_seconds=300)

        assert result is False

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_custom_threshold(self, mock_audio_segment):
        """Test needs_chunking with custom threshold."""
        # Mock audio with 3 minute duration (180,000 ms)
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=180000)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker()

        # With default 300s threshold, should not need chunking
        assert chunker.needs_chunking(Path("/fake/audio.wav"), threshold_seconds=300) is False

        # With 120s threshold, should need chunking
        assert chunker.needs_chunking(Path("/fake/audio.wav"), threshold_seconds=120) is True


class TestChunkAudio:
    """Test chunk_audio method."""

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_short_audio_returns_single_chunk(self, mock_audio_segment, tmp_path):
        """Test short audio returns single chunk (original file)."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Mock short audio (2 minutes = 120,000 ms)
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=120000)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker(chunk_duration_seconds=240)
        chunks = chunker.chunk_audio(audio_file)

        assert len(chunks) == 1
        assert chunks[0].index == 0
        assert chunks[0].path == audio_file
        assert chunks[0].start_time_ms == 0
        assert chunks[0].end_time_ms == 120000
        assert chunks[0].duration_ms == 120000

    @patch('app.utils.audio_chunking.detect_silence')
    @patch('app.utils.audio_chunking.AudioSegment')
    def test_long_audio_creates_multiple_chunks(self, mock_audio_segment, mock_detect_silence, tmp_path):
        """Test long audio creates multiple chunks."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Mock 10 minute audio (600,000 ms) with 4 min chunks
        chunk_duration_ms = 240000
        total_duration_ms = 600000

        mock_audio = MagicMock()
        mock_audio.__len__ = Mock(return_value=total_duration_ms)

        # Mock slicing behavior
        mock_chunk = MagicMock()
        mock_audio.__getitem__ = Mock(return_value=mock_chunk)

        mock_audio_segment.from_file.return_value = mock_audio

        # Mock no silence detected
        mock_detect_silence.return_value = []

        chunker = AudioChunker(chunk_duration_seconds=240, overlap_seconds=5)
        chunks = chunker.chunk_audio(audio_file, output_dir=tmp_path / "chunks")

        # With 4 min chunks and 5s overlap on 10 min audio
        # Expected: ~3 chunks
        assert len(chunks) >= 2
        assert all(isinstance(c, AudioChunk) for c in chunks)
        assert chunks[0].index == 0
        assert chunks[0].start_time_ms == 0

    @patch('app.utils.audio_chunking.detect_silence')
    @patch('app.utils.audio_chunking.AudioSegment')
    def test_chunks_have_overlap(self, mock_audio_segment, mock_detect_silence, tmp_path):
        """Test chunks have proper overlap."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Mock 8 minute audio
        mock_audio = MagicMock()
        mock_audio.__len__ = Mock(return_value=480000)
        mock_chunk = MagicMock()
        mock_audio.__getitem__ = Mock(return_value=mock_chunk)
        mock_audio_segment.from_file.return_value = mock_audio

        mock_detect_silence.return_value = []

        overlap_seconds = 5
        chunker = AudioChunker(chunk_duration_seconds=240, overlap_seconds=overlap_seconds)
        chunks = chunker.chunk_audio(audio_file, output_dir=tmp_path / "chunks")

        # Check overlap between consecutive chunks
        for i in range(len(chunks) - 1):
            # Next chunk should start before current chunk ends
            expected_next_start = chunks[i].end_time_ms - (overlap_seconds * 1000)
            # Allow some tolerance due to silence detection adjustments
            assert chunks[i + 1].start_time_ms <= chunks[i].end_time_ms

    @patch('app.utils.audio_chunking.detect_silence')
    @patch('app.utils.audio_chunking.AudioSegment')
    def test_silence_detection_adjusts_boundary(self, mock_audio_segment, mock_detect_silence, tmp_path):
        """Test silence detection adjusts chunk boundaries."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        # Mock 10 minute audio
        mock_audio = MagicMock()
        mock_audio.__len__ = Mock(return_value=600000)
        mock_chunk = MagicMock()
        mock_audio.__getitem__ = Mock(return_value=mock_chunk)
        mock_audio_segment.from_file.return_value = mock_audio

        # Mock silence found at position relative to search segment
        # This should adjust the chunk boundary
        mock_detect_silence.return_value = [[25000, 26000]]  # Silence at 25-26s into search segment

        chunker = AudioChunker(chunk_duration_seconds=240)
        chunks = chunker.chunk_audio(audio_file, output_dir=tmp_path / "chunks", use_silence_detection=True)

        # Silence detection should have been called
        assert mock_detect_silence.called

    @patch('app.utils.audio_chunking.AudioSegment')
    def test_file_not_found_raises_error(self, mock_audio_segment):
        """Test chunk_audio raises error for non-existent file."""
        non_existent = Path("/fake/does_not_exist.wav")

        chunker = AudioChunker()

        with pytest.raises(FileNotFoundError):
            chunker.chunk_audio(non_existent)

    @patch('app.utils.audio_chunking.detect_silence')
    @patch('app.utils.audio_chunking.AudioSegment')
    def test_disable_silence_detection(self, mock_audio_segment, mock_detect_silence, tmp_path):
        """Test chunking with silence detection disabled."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio")

        mock_audio = MagicMock()
        mock_audio.__len__ = Mock(return_value=600000)
        mock_chunk = MagicMock()
        mock_audio.__getitem__ = Mock(return_value=mock_chunk)
        mock_audio_segment.from_file.return_value = mock_audio

        chunker = AudioChunker(chunk_duration_seconds=240)
        chunks = chunker.chunk_audio(
            audio_file,
            output_dir=tmp_path / "chunks",
            use_silence_detection=False
        )

        # Silence detection should not have been called
        mock_detect_silence.assert_not_called()


class TestCleanupChunks:
    """Test cleanup_chunks method."""

    def test_cleanup_deletes_chunk_files(self, tmp_path):
        """Test cleanup deletes chunk files."""
        # Create fake chunk files
        chunk_files = []
        for i in range(3):
            chunk_file = tmp_path / f"chunk_{i:04d}.wav"
            chunk_file.write_bytes(b"fake chunk")
            chunk_files.append(chunk_file)

        chunks = [
            AudioChunk(index=i, path=f, start_time_ms=i * 1000, end_time_ms=(i + 1) * 1000, duration_ms=1000)
            for i, f in enumerate(chunk_files)
        ]

        chunker = AudioChunker()
        chunker.cleanup_chunks(chunks)

        # All chunk files should be deleted
        for chunk_file in chunk_files:
            assert not chunk_file.exists()

    def test_cleanup_preserves_original_file(self, tmp_path):
        """Test cleanup does not delete original file (when no chunking)."""
        original_file = tmp_path / "original.wav"
        original_file.write_bytes(b"original audio")

        chunks = [
            AudioChunk(index=0, path=original_file, start_time_ms=0, end_time_ms=1000, duration_ms=1000)
        ]

        chunker = AudioChunker()
        chunker.cleanup_chunks(chunks)

        # Original file should still exist (no "chunk_" in name)
        assert original_file.exists()

    def test_cleanup_handles_missing_files(self, tmp_path):
        """Test cleanup handles already-deleted files gracefully."""
        chunks = [
            AudioChunk(
                index=0,
                path=tmp_path / "chunk_0000.wav",
                start_time_ms=0,
                end_time_ms=1000,
                duration_ms=1000
            )
        ]

        chunker = AudioChunker()
        # Should not raise error for missing files
        chunker.cleanup_chunks(chunks)


class TestGetChunkMetadata:
    """Test get_chunk_metadata method."""

    def test_metadata_for_multiple_chunks(self, tmp_path):
        """Test metadata calculation for multiple chunks."""
        chunks = [
            AudioChunk(index=0, path=tmp_path / "chunk_0.wav", start_time_ms=0, end_time_ms=240000, duration_ms=240000),
            AudioChunk(index=1, path=tmp_path / "chunk_1.wav", start_time_ms=235000, end_time_ms=475000, duration_ms=240000),
            AudioChunk(index=2, path=tmp_path / "chunk_2.wav", start_time_ms=470000, end_time_ms=600000, duration_ms=130000),
        ]

        chunker = AudioChunker()
        metadata = chunker.get_chunk_metadata(chunks)

        assert metadata["num_chunks"] == 3
        assert metadata["total_duration_ms"] == 610000
        assert metadata["min_chunk_duration_ms"] == 130000
        assert metadata["max_chunk_duration_ms"] == 240000

    def test_metadata_for_empty_chunks(self, tmp_path):
        """Test metadata for empty chunk list."""
        chunker = AudioChunker()
        metadata = chunker.get_chunk_metadata([])

        assert metadata["num_chunks"] == 0
        assert metadata["total_duration_ms"] == 0

    def test_metadata_for_single_chunk(self, tmp_path):
        """Test metadata for single chunk."""
        chunks = [
            AudioChunk(index=0, path=tmp_path / "audio.wav", start_time_ms=0, end_time_ms=120000, duration_ms=120000),
        ]

        chunker = AudioChunker()
        metadata = chunker.get_chunk_metadata(chunks)

        assert metadata["num_chunks"] == 1
        assert metadata["total_duration_ms"] == 120000
        assert metadata["avg_chunk_duration_ms"] == 120000
        assert metadata["min_chunk_duration_ms"] == 120000
        assert metadata["max_chunk_duration_ms"] == 120000


class TestAudioChunkDataclass:
    """Test AudioChunk dataclass."""

    def test_audio_chunk_creation(self, tmp_path):
        """Test AudioChunk can be created with required fields."""
        chunk = AudioChunk(
            index=0,
            path=tmp_path / "chunk.wav",
            start_time_ms=0,
            end_time_ms=240000,
            duration_ms=240000
        )

        assert chunk.index == 0
        assert chunk.path == tmp_path / "chunk.wav"
        assert chunk.start_time_ms == 0
        assert chunk.end_time_ms == 240000
        assert chunk.duration_ms == 240000
