"""
Unit tests for language validator utility.
"""
import pytest
from app.utils.language_validator import (
    validate_language_code,
    get_supported_languages,
    SUPPORTED_LANGUAGES
)


def test_validate_language_code_valid():
    """Test validation succeeds with valid language codes."""
    # Test common languages
    assert validate_language_code("en") is True
    assert validate_language_code("es") is True
    assert validate_language_code("sl") is True
    assert validate_language_code("auto") is True


def test_validate_language_code_invalid():
    """Test validation fails with invalid language codes."""
    assert validate_language_code("invalid") is False
    assert validate_language_code("xx") is False
    assert validate_language_code("") is False
    assert validate_language_code("EN") is False  # Case-sensitive


def test_validate_language_code_all_supported():
    """Test that all supported languages validate correctly."""
    for lang in SUPPORTED_LANGUAGES:
        assert validate_language_code(lang) is True


def test_get_supported_languages():
    """Test getting list of supported languages."""
    languages = get_supported_languages()

    # Check it's a list
    assert isinstance(languages, list)

    # Check it has expected length (99 + auto)
    assert len(languages) == 100

    # Check common languages are included
    assert "en" in languages
    assert "es" in languages
    assert "sl" in languages
    assert "auto" in languages

    # Check it's a copy (not the original)
    languages.append("test")
    assert "test" not in SUPPORTED_LANGUAGES


def test_supported_languages_constant():
    """Test SUPPORTED_LANGUAGES constant has expected properties."""
    # Check it's a list
    assert isinstance(SUPPORTED_LANGUAGES, list)

    # Check length
    assert len(SUPPORTED_LANGUAGES) == 100

    # Check no duplicates
    assert len(SUPPORTED_LANGUAGES) == len(set(SUPPORTED_LANGUAGES))

    # Check auto is included
    assert "auto" in SUPPORTED_LANGUAGES

    # Check all are lowercase strings
    for lang in SUPPORTED_LANGUAGES:
        assert isinstance(lang, str)
        assert lang == lang.lower()
        assert len(lang) >= 2  # At least 2 characters
