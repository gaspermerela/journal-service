"""
Slovenian spell-check service using SymSpellPy with Sloleks dictionary.
"""
import pickle
import re
import time
from pathlib import Path
from typing import List, Optional

from symspellpy import SymSpell, Verbosity

from app.config import settings
from app.schemas.spellcheck import SpellingIssue
from app.services.spellcheck_base import SpellCheckService
from app.utils.logger import get_logger


logger = get_logger("services.spellcheck_slovenian")

# Regex pattern for tokenizing Slovenian text
# Matches words with Slovenian characters (č, š, ž and their uppercase variants)
SLOVENIAN_WORD_PATTERN = re.compile(r"\b[a-zA-ZčšžČŠŽ]+\b")


class SlovenianSpellCheckService(SpellCheckService):
    """
    Slovenian spell-check service using SymSpellPy.

    Loads dictionary from pickle if available (fast ~2-5s),
    otherwise builds from word list and saves pickle (~60-90s).
    """

    LANGUAGE_CODE = "sl"

    def __init__(
        self,
        wordlist_path: Optional[str] = None,
        pickle_path: Optional[str] = None,
        max_edit_distance: Optional[int] = None,
        prefix_length: Optional[int] = None,
        suggestion_count: Optional[int] = None,
        min_word_length: Optional[int] = None,
    ):
        """
        Initialize Slovenian spell-check service.

        Args:
            wordlist_path: Path to word list file (one word per line)
            pickle_path: Path to pickle file for fast loading
            max_edit_distance: Maximum edit distance for suggestions (default from config)
            prefix_length: SymSpell optimization parameter (default from config)
            suggestion_count: Maximum suggestions per word (default from config)
            min_word_length: Skip words shorter than this (default from config)
        """
        self._symspell: Optional[SymSpell] = None
        self._loaded = False

        # Paths - use provided or fall back to config
        # Word list: from image (SPELLCHECK_WORDLIST_PATH)
        # Pickle: from mounted cache volume (SPELLCHECK_CACHE_PATH)
        self._wordlist_path = Path(wordlist_path) if wordlist_path else Path(settings.SPELLCHECK_WORDLIST_PATH)
        cache_path = Path(settings.SPELLCHECK_CACHE_PATH)
        self._pickle_path = Path(pickle_path) if pickle_path else cache_path / "symspell_sl.pkl"

        # Configuration - use provided or fall back to config
        self._max_edit_distance = max_edit_distance or settings.SPELLCHECK_MAX_EDIT_DISTANCE
        self._prefix_length = prefix_length or settings.SPELLCHECK_PREFIX_LENGTH
        self._suggestion_count = suggestion_count or settings.SPELLCHECK_SUGGESTION_COUNT
        self._min_word_length = min_word_length or settings.SPELLCHECK_MIN_WORD_LENGTH

        logger.info(
            "Slovenian spell-check service initialized",
            wordlist_path=str(self._wordlist_path),
            pickle_path=str(self._pickle_path),
            max_edit_distance=self._max_edit_distance,
            prefix_length=self._prefix_length,
            suggestion_count=self._suggestion_count,
            min_word_length=self._min_word_length,
        )

    def load(self) -> bool:
        """
        Load dictionary from pickle or build from word list.

        Returns:
            True if loaded successfully, False otherwise
        """
        if self._loaded:
            return True

        # Try loading from pickle first (fast)
        if self._pickle_path.exists():
            if self._load_from_pickle():
                return True
            # If pickle loading failed, try word list

        # Fall back to building from word list
        if self._wordlist_path.exists():
            return self._build_from_wordlist()

        logger.error(
            "Neither pickle nor word list found",
            pickle_path=str(self._pickle_path),
            wordlist_path=str(self._wordlist_path),
        )
        return False

    def _load_from_pickle(self) -> bool:
        """Load SymSpell from pickle file."""
        try:
            start_time = time.time()

            with open(self._pickle_path, "rb") as f:
                self._symspell = pickle.load(f)

            self._loaded = True
            load_time = time.time() - start_time

            logger.info(
                "Slovenian dictionary loaded from pickle",
                load_time_seconds=round(load_time, 2),
                pickle_path=str(self._pickle_path),
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to load pickle, will try word list",
                error=str(e),
                pickle_path=str(self._pickle_path),
            )
            return False

    def _build_from_wordlist(self) -> bool:
        """Build SymSpell dictionary from word list and save pickle."""
        try:
            start_time = time.time()

            self._symspell = SymSpell(
                max_dictionary_edit_distance=self._max_edit_distance,
                prefix_length=self._prefix_length,
            )

            # Load word list - one word per line, no frequency data
            # Using create_dictionary_entry for each word (more reliable than load_dictionary)
            word_count = 0
            with open(self._wordlist_path, "r", encoding="utf-8") as f:
                for line in f:
                    word = line.strip()
                    if word:  # Skip empty lines
                        # Use count=1 for all words (no frequency data available)
                        self._symspell.create_dictionary_entry(word, 1)
                        word_count += 1

            if word_count == 0:
                logger.error(
                    "No words loaded from word list",
                    wordlist_path=str(self._wordlist_path),
                )
                return False

            build_time = time.time() - start_time

            logger.info(
                "Slovenian dictionary built from word list",
                word_count=word_count,
                build_time_seconds=round(build_time, 2),
                wordlist_path=str(self._wordlist_path),
            )

            # Save pickle for fast loading next time
            self._save_pickle()
            self._loaded = True
            return True

        except Exception as e:
            logger.error(
                "Failed to build dictionary from word list",
                error=str(e),
                wordlist_path=str(self._wordlist_path),
                exc_info=True,
            )
            return False

    def _save_pickle(self) -> None:
        """Save SymSpell to pickle file for fast loading."""
        try:
            # Ensure directory exists
            self._pickle_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._pickle_path, "wb") as f:
                pickle.dump(self._symspell, f)

            logger.info(
                "Slovenian dictionary saved to pickle",
                pickle_path=str(self._pickle_path),
            )

        except Exception as e:
            logger.warning(
                "Failed to save pickle (will rebuild on next start)",
                error=str(e),
                pickle_path=str(self._pickle_path),
            )

    # TODO: measure time and parallelize
    def check_text(self, text: str) -> List[SpellingIssue]:
        """
        Check text for spelling issues.

        Args:
            text: Text to check

        Returns:
            Deduplicated list of misspelled words with suggestions
        """
        if not self._loaded or self._symspell is None:
            logger.warning("Spell-check called but dictionary not loaded")
            return []

        # Tokenize text into words
        words = self._tokenize(text)

        # Track unique misspelled words (deduplicate)
        issues: dict[str, List[str]] = {}

        for word in words:
            # Skip short words
            if len(word) < self._min_word_length:
                continue

            # Normalize to lowercase for lookup
            word_lower = word.lower()

            # Skip if already processed
            if word_lower in issues:
                continue

            # Check if word is in dictionary
            suggestions = self._symspell.lookup(
                word_lower,
                Verbosity.CLOSEST,
                max_edit_distance=self._max_edit_distance,
            )

            # If word is correctly spelled, lookup returns the word itself as first suggestion
            # Only report if misspelled (first suggestion differs) and we have suggestions
            if suggestions and suggestions[0].term != word_lower:
                suggestion_terms = [s.term for s in suggestions[: self._suggestion_count]]
                issues[word_lower] = suggestion_terms

        return [
            SpellingIssue(word=word, suggestions=suggestions)
            for word, suggestions in issues.items()
        ]

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text into words.

        Extracts words using regex pattern that handles Slovenian characters.

        Args:
            text: Text to tokenize

        Returns:
            List of words (preserving original case)
        """
        return SLOVENIAN_WORD_PATTERN.findall(text)

    def is_loaded(self) -> bool:
        """Check if dictionary is loaded."""
        return self._loaded

    def get_language(self) -> str:
        """Get language code."""
        return self.LANGUAGE_CODE
