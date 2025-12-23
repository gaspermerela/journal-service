"""
Pydantic schemas for spell-check functionality.
"""
from typing import List

from pydantic import BaseModel, Field


class SpellingIssue(BaseModel):
    """A spelling issue with suggested corrections."""

    word: str = Field(description="Misspelled word (lowercase)")
    suggestions: List[str] = Field(description="Suggested corrections ordered by relevance")
