"""
Spell-check service factory and singleton management.
"""
from typing import Optional

from app.services.spellcheck_slovenian import SlovenianSpellCheckService
from app.utils.logger import get_logger

logger = get_logger("services.spellcheck")

# Singleton instances for each supported language
_slovenian_service: Optional[SlovenianSpellCheckService] = None

def get_slovenian_spellcheck_service() -> Optional[SlovenianSpellCheckService]:
    """
    Get the singleton Slovenian spell-check service.

    Returns:
        SlovenianSpellCheckService instance if initialized, None otherwise
    """
    global _slovenian_service
    return _slovenian_service


def initialize_slovenian_spellcheck() -> bool:
    """
    Initialize the Slovenian spell-check service singleton.

    Called during app startup to pre-load the dictionary.

    Returns:
        True if initialized successfully, False otherwise
    """
    global _slovenian_service

    logger.info("Initializing Slovenian spell-check service...")
    _slovenian_service = SlovenianSpellCheckService()

    if _slovenian_service.load():
        logger.info("Slovenian spell-check service initialized successfully")
        return True
    else:
        logger.warning("Failed to initialize Slovenian spell-check service")
        _slovenian_service = None
        return False
