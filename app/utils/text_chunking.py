"""
Text chunking utilities for splitting long texts at sentence boundaries.

Used to prevent LLM hallucination with long transcriptions (>500 words).
"""
import logging
import re
from typing import List

logger = logging.getLogger(__name__)

# Regex pattern for sentence boundary detection
# Matches: period/exclamation/question followed by whitespace and capital letter
SENTENCE_END_PATTERN = re.compile(
    r'(?<=[.!?])'           # Lookbehind for sentence-ending punctuation
    r'(?:\s*["\'])?'        # Optional closing quote
    r'\s+'                  # Required whitespace
    r'(?=[A-Z"\'])'         # Lookahead for capital letter or opening quote
)


def count_words(text: str) -> int:
    """
    Count words in text using simple whitespace splitting.

    Args:
        text: Input text

    Returns:
        Word count
    """
    if not text:
        return 0
    return len(text.split())


def split_into_sentences(text: str) -> List[str]:
    """
    Split text into sentences using regex pattern.

    Optimized for spoken transcriptions which may have:
    - Incomplete punctuation
    - Run-on sentences
    - Casual speech patterns

    Args:
        text: Input text to split

    Returns:
        List of sentences
    """
    if not text or not text.strip():
        return []

    # Split on sentence boundaries
    sentences = SENTENCE_END_PATTERN.split(text)

    # Filter empty strings and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]

    if not sentences:
        return [text.strip()]

    return sentences


def create_chunks(text: str, max_words: int = 500) -> List[str]:
    """
    Split text into chunks that don't exceed max_words.

    Strategy:
    1. Split text into sentences
    2. Group sentences into chunks without exceeding max_words
    3. Each sentence boundary is respected

    Args:
        text: Input text to chunk
        max_words: Maximum words per chunk (default: 500)

    Returns:
        List of text chunks
    """
    word_count = count_words(text)

    # No chunking needed if under threshold
    if word_count <= max_words:
        logger.debug(
            f"Text under threshold, no chunking needed (word_count={word_count}, threshold={max_words})"
        )
        return [text]

    sentences = split_into_sentences(text)

    if len(sentences) <= 1:
        # Can't split further, return as single chunk (may exceed max_words)
        logger.warning(
            f"Cannot split text into sentences, returning as single chunk (word_count={word_count})"
        )
        return [text]

    chunks = []
    current_chunk_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = count_words(sentence)

        # Check if adding this sentence would exceed limit
        if current_word_count + sentence_words > max_words and current_chunk_sentences:
            # Save current chunk
            chunks.append(" ".join(current_chunk_sentences))

            # Start new chunk
            current_chunk_sentences = []
            current_word_count = 0

        current_chunk_sentences.append(sentence)
        current_word_count += sentence_words

    # Don't forget the last chunk
    if current_chunk_sentences:
        chunks.append(" ".join(current_chunk_sentences))

    logger.info(
        f"Text chunked successfully (original_words={word_count}, chunk_count={len(chunks)}, max_words={max_words})"
    )

    return chunks


def reassemble_cleaned_chunks(chunks: List[str]) -> str:
    """
    Reassemble cleaned chunks into a single text.

    Joins chunks directly with a space, preserving LLM output exactly.

    Args:
        chunks: List of cleaned text chunks

    Returns:
        Combined text
    """
    if not chunks:
        return ""

    if len(chunks) == 1:
        return chunks[0]

    # Join chunks directly with space (no added paragraph breaks)
    return " ".join(chunk.strip() for chunk in chunks)
