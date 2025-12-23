"""
Abstract base class for spell-check services.
"""
from abc import ABC, abstractmethod
from typing import List

from app.schemas.spellcheck import SpellingIssue


class SpellCheckService(ABC):
    """
    Abstract base class for spell-check service implementations.

    Concrete implementations should handle loading dictionaries and
    checking text for spelling issues.
    """

    @abstractmethod
    def check_text(self, text: str) -> List[SpellingIssue]:
        """
        Check text for spelling issues and return suggestions.

        Args:
            text: Text to check for spelling errors

        Returns:
            List of SpellingIssue objects, deduplicated by word
        """
        pass

    @abstractmethod
    def is_loaded(self) -> bool:
        """Check if the dictionary is loaded and ready."""
        pass

    @abstractmethod
    def get_language(self) -> str:
        """Get the language code this service handles (e.g., 'sl' for Slovenian)."""
        pass

    @abstractmethod
    def load(self) -> bool:
        """
        Load the dictionary.

        Returns:
            True if loaded successfully, False otherwise
        """
        pass
