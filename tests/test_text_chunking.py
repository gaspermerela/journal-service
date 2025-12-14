"""
Unit tests for text chunking utility.

These tests are designed to run standalone without the full app config.
"""
import sys
import os

# Add project root to path for standalone import
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from app.utils.text_chunking import (
    count_words,
    split_into_sentences,
    create_chunks,
    reassemble_cleaned_chunks
)


class TestCountWords:
    """Tests for count_words function."""

    def test_simple_text(self):
        assert count_words("Hello world") == 2

    def test_empty_text(self):
        assert count_words("") == 0

    def test_none_is_empty(self):
        # Empty string should return 0
        assert count_words("") == 0

    def test_multiple_spaces(self):
        assert count_words("Hello   world") == 2

    def test_newlines(self):
        assert count_words("Hello\nworld\ntest") == 3

    def test_tabs(self):
        assert count_words("Hello\tworld") == 2

    def test_long_text(self):
        text = " ".join(["word"] * 100)
        assert count_words(text) == 100


class TestSplitIntoSentences:
    """Tests for split_into_sentences function."""

    def test_simple_sentences(self):
        text = "First sentence. Second sentence. Third sentence."
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_exclamation_marks(self):
        text = "Wow! Amazing! Incredible!"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_question_marks(self):
        text = "What happened? I don't know. Really?"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_mixed_punctuation(self):
        text = "Hello there. How are you? Great!"
        sentences = split_into_sentences(text)
        assert len(sentences) == 3

    def test_no_punctuation(self):
        text = "This text has no punctuation at all"
        sentences = split_into_sentences(text)
        assert len(sentences) == 1
        assert sentences[0] == text

    def test_empty_text(self):
        assert split_into_sentences("") == []

    def test_whitespace_only(self):
        assert split_into_sentences("   ") == []

    def test_lowercase_after_period(self):
        # Should not split on abbreviations like "e.g." or "i.e."
        text = "This is a test. but this continues"
        sentences = split_into_sentences(text)
        # Should be 1 sentence because 'but' is lowercase
        assert len(sentences) == 1

    def test_quoted_sentence(self):
        text = 'He said "Hello." She replied "Hi."'
        sentences = split_into_sentences(text)
        assert len(sentences) >= 1  # May or may not split depending on pattern


class TestCreateChunks:
    """Tests for create_chunks function."""

    def test_short_text_no_chunking(self):
        text = "Short text under threshold."
        chunks = create_chunks(text, max_words=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_exactly_at_threshold(self):
        # 500 words exactly
        text = " ".join(["word"] * 500)
        chunks = create_chunks(text, max_words=500)
        assert len(chunks) == 1

    def test_just_over_threshold_no_sentences(self):
        # Text without sentence boundaries can't be split
        text = " ".join(["word"] * 600)
        chunks = create_chunks(text, max_words=500)
        # Should return single chunk since no sentence boundaries
        assert len(chunks) == 1

    def test_chunking_with_sentences(self):
        # Create text with clear sentence boundaries
        sentences = []
        for i in range(20):
            sentences.append(f"This is sentence number {i} with some extra words to pad it out.")
        text = " ".join(sentences)

        # Each sentence is roughly 12-13 words, so 20 sentences = ~250 words
        # Let's set a low threshold to force chunking
        chunks = create_chunks(text, max_words=50)
        assert len(chunks) > 1

    def test_respects_sentence_boundaries(self):
        # Create text where each sentence is about 30 words
        sentence1 = "The quick brown fox jumps over the lazy dog and then runs away into the forest. "
        sentence2 = "Meanwhile the cat watches from the window sill wondering what all the fuss is about. "
        sentence3 = "Later that day everyone gathered around for dinner at the old farmhouse. "

        text = sentence1 + sentence2 + sentence3
        chunks = create_chunks(text, max_words=40)

        # Each chunk should end with a complete sentence (period)
        for chunk in chunks:
            assert chunk.strip().endswith(".")

    def test_very_low_threshold(self):
        text = "First sentence here. Second sentence here. Third sentence here."
        chunks = create_chunks(text, max_words=5)
        # With 5 word threshold, each sentence should be its own chunk
        assert len(chunks) == 3

    def test_empty_text(self):
        chunks = create_chunks("", max_words=500)
        assert len(chunks) == 1
        assert chunks[0] == ""

    def test_single_long_sentence(self):
        # Very long sentence that exceeds threshold but can't be split
        words = ["word"] * 600
        text = " ".join(words) + "."
        chunks = create_chunks(text, max_words=500)
        # Can't split within a sentence, returns as-is
        assert len(chunks) == 1


class TestReassembleCleanedChunks:
    """Tests for reassemble_cleaned_chunks function."""

    def test_single_chunk(self):
        chunks = ["Only one chunk here."]
        result = reassemble_cleaned_chunks(chunks)
        assert result == "Only one chunk here."

    def test_multiple_chunks(self):
        chunks = ["First chunk.", "Second chunk.", "Third chunk."]
        result = reassemble_cleaned_chunks(chunks)
        assert "First chunk." in result
        assert "Second chunk." in result
        assert "Third chunk." in result
        # Should be joined with single space
        assert result == "First chunk. Second chunk. Third chunk."

    def test_empty_list(self):
        result = reassemble_cleaned_chunks([])
        assert result == ""

    def test_strips_whitespace(self):
        chunks = ["  First chunk.  ", "  Second chunk.  "]
        result = reassemble_cleaned_chunks(chunks)
        assert result == "First chunk. Second chunk."

    def test_preserves_internal_whitespace(self):
        chunks = ["First\nchunk.", "Second\nchunk."]
        result = reassemble_cleaned_chunks(chunks)
        # Internal newlines should be preserved
        assert "First\nchunk." in result


class TestEndToEndChunking:
    """Integration tests for the full chunking workflow."""

    def test_full_workflow_short_text(self):
        """Short text should pass through unchanged."""
        original = "This is a short dream about flying. I was soaring above the clouds."

        # Process
        word_count = count_words(original)
        assert word_count < 500

        chunks = create_chunks(original, max_words=500)
        assert len(chunks) == 1

        # Simulate cleanup (just uppercase for test)
        cleaned_chunks = [chunk.upper() for chunk in chunks]

        # Reassemble
        result = reassemble_cleaned_chunks(cleaned_chunks)
        assert result == original.upper()

    def test_full_workflow_long_text(self):
        """Long text should be chunked and reassembled."""
        # Create a "transcription" with multiple sentences
        sentences = [
            "I had a vivid dream last night about a mysterious forest.",
            "The trees were enormous and glowing with an ethereal light.",
            "I walked along a winding path that seemed to go on forever.",
            "Strange creatures watched me from the shadows.",
            "Then suddenly I found myself in a vast meadow.",
            "The sky above was filled with swirling colors.",
            "I felt a deep sense of peace and wonder.",
            "A voice called my name from somewhere far away.",
            "I tried to follow the voice but could not move.",
            "Then I woke up with the sunrise streaming through my window."
        ]
        original = " ".join(sentences)

        # Process with low threshold to force chunking
        chunks = create_chunks(original, max_words=30)
        assert len(chunks) > 1

        # Simulate cleanup
        cleaned_chunks = [chunk.upper() for chunk in chunks]

        # Reassemble
        result = reassemble_cleaned_chunks(cleaned_chunks)

        # Should have all content
        assert "VIVID DREAM" in result
        assert "SUNRISE" in result
