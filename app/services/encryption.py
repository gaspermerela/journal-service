"""
Encryption service for sensitive data (API keys, tokens, etc.)

Uses Fernet symmetric encryption with per-user key derivation via PBKDF2.
Each user's data is encrypted with a unique key derived from:
- Application secret (ENCRYPTION_KEY or JWT_SECRET_KEY)
- User's UUID (stable, never changes)

This ensures:
- User data isolation (different encryption keys per user)
- Defense in depth (attacker needs both DB and app secret)
"""

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.fernet import Fernet, InvalidToken
import base64
from uuid import UUID
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("encryption")


def _derive_key(user_id: UUID) -> bytes:
    """
    Derive encryption key from user_id + app secret.

    This creates a stable, per-user encryption key that:
    - Never changes (based on immutable user_id)
    - Is unique per user (different salt)
    - Requires both DB access AND app secret to decrypt

    Args:
        user_id: User's UUID for key derivation (used as salt)

    Returns:
        32-byte encryption key suitable for Fernet

    Technical details:
    - Algorithm: PBKDF2-HMAC-SHA256
    - Iterations: 100,000 (OWASP recommendation for 2025)
    - Salt: User UUID (stable per user)
    - Master key: settings.api_encryption_key
    """
    salt = str(user_id).encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,  # Fernet requires exactly 32 bytes
        salt=salt,
        iterations=100000,  # OWASP recommendation
    )

    derived_key = kdf.derive(settings.api_encryption_key.encode())
    return base64.urlsafe_b64encode(derived_key)


def encrypt_notion_key(api_key: str, user_id: UUID) -> str:
    """
    Encrypt Notion API key for database storage.

    Args:
        api_key: Plaintext Notion API key (e.g., "secret_xxx...")
        user_id: User's UUID for key derivation

    Returns:
        Base64-encoded encrypted string safe for database storage

    Raises:
        ValueError: If api_key is empty or invalid
        Exception: If encryption fails

    Example:
        >>> encrypted = encrypt_notion_key("secret_abc123", user.id)
        >>> # Store encrypted value in database
        >>> user.notion_api_key_encrypted = encrypted
    """
    if not api_key or not api_key.strip():
        raise ValueError("API key cannot be empty")

    try:
        key = _derive_key(user_id)
        fernet = Fernet(key)
        encrypted = fernet.encrypt(api_key.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Failed to encrypt API key for user {user_id}: {e}")
        raise


def decrypt_notion_key(encrypted_key: str, user_id: UUID) -> str:
    """
    Decrypt Notion API key for use.

    Args:
        encrypted_key: Base64-encoded encrypted key from DB
        user_id: User's UUID for key derivation

    Returns:
        Plaintext Notion API key

    Raises:
        InvalidToken: If decryption fails (wrong key, corrupted data, etc.)
        ValueError: If encrypted_key is empty

    Example:
        >>> user = await get_user(user_id)
        >>> api_key = decrypt_notion_key(user.notion_api_key_encrypted, user.id)
        >>> # Use api_key for Notion API calls
        >>> notion_client = Client(auth=api_key)
    """
    if not encrypted_key or not encrypted_key.strip():
        raise ValueError("Encrypted key cannot be empty")

    try:
        key = _derive_key(user_id)
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_key.encode())
        return decrypted.decode()
    except InvalidToken as e:
        logger.error(f"Failed to decrypt API key for user {user_id}: Invalid token")
        raise ValueError("Failed to decrypt API key - key may be corrupted or encryption key changed") from e
    except Exception as e:
        logger.error(f"Failed to decrypt API key for user {user_id}: {e}")
        raise


def verify_encryption(plaintext: str, user_id: UUID) -> bool:
    """
    Verify encryption/decryption works correctly.

    Useful for testing and debugging encryption configuration.

    Args:
        plaintext: Test string to encrypt/decrypt
        user_id: User's UUID

    Returns:
        True if round-trip encryption works correctly

    Example:
        >>> if verify_encryption("test", user.id):
        >>>     print("Encryption is working correctly")
    """
    try:
        encrypted = encrypt_notion_key(plaintext, user_id)
        decrypted = decrypt_notion_key(encrypted, user_id)
        return decrypted == plaintext
    except Exception as e:
        logger.error(f"Encryption verification failed: {e}")
        return False
