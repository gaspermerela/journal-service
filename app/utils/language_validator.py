"""
Language code validation utilities for Whisper transcription.
"""
from typing import List

# Whisper supports 99 languages + auto-detection
# Source: https://github.com/openai/whisper#available-models-and-languages
SUPPORTED_LANGUAGES: List[str] = [
    "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr",
    "pl", "ca", "nl", "ar", "sv", "it", "id", "hi", "fi", "vi",
    "he", "uk", "el", "ms", "cs", "ro", "da", "hu", "ta", "no",
    "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy", "sk",
    "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk",
    "br", "eu", "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw",
    "gl", "mr", "pa", "si", "km", "sn", "yo", "so", "af", "oc",
    "ka", "be", "tg", "sd", "gu", "am", "yi", "lo", "uz", "fo",
    "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl",
    "mg", "as", "tt", "haw", "ln", "ha", "ba", "jw", "su", "auto"
]


def validate_language_code(language: str) -> bool:
    """
    Validate if a language code is supported by Whisper.

    Args:
        language: Language code to validate (e.g., 'en', 'es', 'auto')

    Returns:
        True if language is supported, False otherwise

    Example:
        >>> validate_language_code("en")
        True
        >>> validate_language_code("auto")
        True
        >>> validate_language_code("invalid")
        False
    """
    return language in SUPPORTED_LANGUAGES


def get_supported_languages() -> List[str]:
    """
    Get list of all supported language codes.

    Returns:
        List of ISO language codes plus 'auto' for automatic detection

    Example:
        >>> langs = get_supported_languages()
        >>> "en" in langs
        True
        >>> len(langs)
        100
    """
    return SUPPORTED_LANGUAGES.copy()
