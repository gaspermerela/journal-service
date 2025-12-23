"""
Unit tests for spell-check service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.spellcheck_slovenian import (
    SlovenianSpellCheckService,
    SLOVENIAN_WORD_PATTERN,
)
from app.schemas.spellcheck import SpellingIssue


class TestSlovenianWordPattern:
    """Tests for the Slovenian word tokenization regex."""

    def test_tokenize_basic_words(self):
        """Test tokenization of basic Latin characters."""
        text = "To je primer"
        words = SLOVENIAN_WORD_PATTERN.findall(text)
        assert words == ["To", "je", "primer"]

    def test_tokenize_slovenian_characters(self):
        """Test tokenization handles Slovenian special characters (č, š, ž)."""
        text = "čudovit šumnik žaba"
        words = SLOVENIAN_WORD_PATTERN.findall(text)
        assert "čudovit" in words
        assert "šumnik" in words
        assert "žaba" in words

    def test_tokenize_uppercase_slovenian_characters(self):
        """Test tokenization handles uppercase Slovenian characters."""
        text = "ČŠŽČŠŽ Čudovit"
        words = SLOVENIAN_WORD_PATTERN.findall(text)
        assert "ČŠŽČŠŽ" in words
        assert "Čudovit" in words

    def test_tokenize_mixed_punctuation(self):
        """Test tokenization ignores punctuation."""
        text = "Zdravo, svet! Kako si?"
        words = SLOVENIAN_WORD_PATTERN.findall(text)
        assert words == ["Zdravo", "svet", "Kako", "si"]

    def test_tokenize_numbers_excluded(self):
        """Test that numbers are excluded from tokenization."""
        text = "Imam 5 jabolk in 10 hrušk"
        words = SLOVENIAN_WORD_PATTERN.findall(text)
        assert "5" not in words
        assert "10" not in words
        assert "Imam" in words
        assert "jabolk" in words


class TestSlovenianSpellCheckService:
    """Tests for SlovenianSpellCheckService."""

    def test_check_text_returns_empty_when_not_loaded(self):
        """Test graceful handling when dictionary not loaded."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        # Don't call load() - dictionary should not be loaded
        result = service.check_text("neki tekst")
        assert result == []

    def test_is_loaded_returns_false_initially(self):
        """Test is_loaded() returns False before loading."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        assert service.is_loaded() is False

    def test_get_language_returns_sl(self):
        """Test get_language() returns 'sl'."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        assert service.get_language() == "sl"

    def test_deduplication_of_repeated_misspellings(self):
        """Test same misspelled word appears only once in results."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        service._loaded = True

        # Mock SymSpell
        mock_symspell = Mock()
        # Return suggestions for unknown word
        mock_suggestion = Mock()
        mock_suggestion.term = "napako"
        mock_symspell.lookup.return_value = [mock_suggestion]
        service._symspell = mock_symspell

        text = "napaka napaka napaka napaka"
        result = service.check_text(text)

        # Should only have one entry for "napaka"
        assert len(result) == 1
        assert result[0].word == "napaka"

    def test_skip_short_words(self):
        """Test words shorter than min_length are skipped."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
            min_word_length=3,
        )
        service._loaded = True

        # Mock SymSpell to return empty (no suggestions = not in dictionary)
        mock_symspell = Mock()
        mock_symspell.lookup.return_value = []
        service._symspell = mock_symspell

        text = "to je a"  # All words < 3 chars
        result = service.check_text(text)

        # All words should be skipped due to min_word_length
        assert len(result) == 0
        # lookup should never be called
        mock_symspell.lookup.assert_not_called()

    def test_correct_word_not_reported(self):
        """Test correctly spelled words are not reported."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        service._loaded = True

        # Mock SymSpell to return the word itself (indicating it's correct)
        mock_symspell = Mock()
        mock_suggestion = Mock()
        mock_suggestion.term = "danes"
        mock_symspell.lookup.return_value = [mock_suggestion]
        service._symspell = mock_symspell

        text = "danes"
        result = service.check_text(text)

        # Word is in dictionary, should not be reported
        assert len(result) == 0

    def test_misspelled_word_with_suggestions(self):
        """Test misspelled words are reported with suggestions."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
            suggestion_count=3,
        )
        service._loaded = True

        # Mock SymSpell to return different suggestions (word not in dictionary)
        mock_symspell = Mock()
        suggestion1 = Mock(term="napako")
        suggestion2 = Mock(term="napaka")
        suggestion3 = Mock(term="napaki")
        mock_symspell.lookup.return_value = [suggestion1, suggestion2, suggestion3]
        service._symspell = mock_symspell

        text = "napako"  # This is actually correct but we're simulating misspelling
        # For the test, we need to simulate a word not in dictionary
        # Let's use "napka" which would return suggestions like above
        text = "napka"
        result = service.check_text(text)

        assert len(result) == 1
        assert result[0].word == "napka"
        assert len(result[0].suggestions) == 3
        assert "napako" in result[0].suggestions

    def test_tokenize_preserves_original_case_for_display(self):
        """Test _tokenize preserves original case."""
        service = SlovenianSpellCheckService(
            wordlist_path="/nonexistent/path.txt",
            pickle_path="/nonexistent/pickle.pkl",
        )
        text = "Ljubljana SLOVENIJA čudovito"
        tokens = service._tokenize(text)
        assert "Ljubljana" in tokens
        assert "SLOVENIJA" in tokens
        assert "čudovito" in tokens


class TestSpellingIssueSchema:
    """Tests for SpellingIssue Pydantic schema."""

    def test_create_spelling_issue(self):
        """Test creating a SpellingIssue instance."""
        issue = SpellingIssue(word="napka", suggestions=["napako", "napaka"])
        assert issue.word == "napka"
        assert issue.suggestions == ["napako", "napaka"]

    def test_spelling_issue_serialization(self):
        """Test SpellingIssue JSON serialization."""
        issue = SpellingIssue(word="čudovit", suggestions=["čudovito", "čudovita"])
        data = issue.model_dump()
        assert data == {
            "word": "čudovit",
            "suggestions": ["čudovito", "čudovita"],
        }

    def test_spelling_issue_empty_suggestions(self):
        """Test SpellingIssue with empty suggestions list."""
        issue = SpellingIssue(word="unknown", suggestions=[])
        assert issue.word == "unknown"
        assert issue.suggestions == []
