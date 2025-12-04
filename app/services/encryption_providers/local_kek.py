"""
Local Key Encryption Key (KEK) provider.

Uses a local master key with PBKDF2 key derivation to create per-user KEKs.
DEKs are encrypted using AES-256-GCM for authenticated encryption.

Security properties:
- Per-user key isolation via PBKDF2 with user UUID as salt
- 100,000 PBKDF2 iterations (OWASP 2025 recommendation)
- AES-256-GCM provides authenticated encryption (confidentiality + integrity)
- 96-bit random nonce per encryption (prepended to ciphertext)

This is the Phase 1 implementation designed for easy migration to cloud KMS.
"""

import os
from uuid import UUID

from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.services.encryption_providers.base import KEKProvider
from app.utils.logger import get_logger

logger = get_logger("encryption.local_kek")


class LocalKEKProviderError(Exception):
    """Base exception for LocalKEKProvider errors."""
    pass


class LocalKEKProvider(KEKProvider):
    """
    Local KEK provider using PBKDF2 key derivation + AES-GCM encryption.

    Derives a unique KEK per user from the application master key.
    This implementation can be replaced with cloud KMS providers
    without changing the envelope encryption service interface.

    Key derivation:
        KEK = PBKDF2(master_key, salt=user_uuid, iterations=100000, hash=SHA256)

    DEK encryption:
        ciphertext = AES-256-GCM(KEK, nonce=random_96bit, plaintext=DEK)
        output = nonce || ciphertext (nonce prepended)

    Thread Safety:
        This class is thread-safe. Key derivation and encryption are
        stateless operations.

    Example:
        >>> provider = LocalKEKProvider(master_key=settings.api_encryption_key)
        >>> dek = os.urandom(32)
        >>> encrypted = await provider.encrypt_dek(dek, user_id)
        >>> decrypted = await provider.decrypt_dek(encrypted, user_id)
        >>> assert dek == decrypted
    """

    VERSION = "local-v1"
    PBKDF2_ITERATIONS = 100000  # OWASP 2025 recommendation
    KEK_LENGTH = 32  # AES-256
    NONCE_LENGTH = 12  # 96 bits for GCM

    def __init__(self, master_key: str):
        """
        Initialize with master key from application settings.

        Args:
            master_key: Master encryption key string (from settings.api_encryption_key)

        Raises:
            ValueError: If master_key is empty or too short
        """
        if not master_key or len(master_key) < 16:
            raise ValueError("Master key must be at least 16 characters")

        self._master_key = master_key.encode("utf-8")
        logger.info("LocalKEKProvider initialized", version=self.VERSION)

    def _derive_kek(self, user_id: UUID) -> bytes:
        """
        Derive user-specific KEK from master key.

        Uses PBKDF2-HMAC-SHA256 with the user's UUID as salt.
        This ensures each user has a unique KEK while only requiring
        a single master key.

        Args:
            user_id: User UUID used as salt for key derivation

        Returns:
            32-byte AES-256 key
        """
        salt = str(user_id).encode("utf-8")

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=self.KEK_LENGTH,
            salt=salt,
            iterations=self.PBKDF2_ITERATIONS,
        )

        return kdf.derive(self._master_key)

    async def encrypt_dek(self, dek: bytes, user_id: UUID) -> bytes:
        """
        Encrypt a DEK using the user's derived KEK via AES-256-GCM.

        Output format: nonce (12 bytes) || ciphertext || tag (16 bytes)

        Args:
            dek: Raw Data Encryption Key (should be 32 bytes for AES-256)
            user_id: User UUID for per-user key derivation

        Returns:
            Encrypted DEK with prepended nonce

        Raises:
            ValueError: If dek is empty
            LocalKEKProviderError: If encryption fails
        """
        if not dek:
            raise ValueError("DEK cannot be empty")

        try:
            kek = self._derive_kek(user_id)
            aesgcm = AESGCM(kek)

            # Generate random nonce for each encryption
            nonce = os.urandom(self.NONCE_LENGTH)

            # Encrypt DEK (ciphertext includes authentication tag)
            ciphertext = aesgcm.encrypt(nonce, dek, None)

            # Return nonce || ciphertext
            return nonce + ciphertext

        except Exception as e:
            logger.error(
                "Failed to encrypt DEK",
                user_id=str(user_id),
                error=str(e),
            )
            raise LocalKEKProviderError(f"DEK encryption failed: {e}") from e

    async def decrypt_dek(self, encrypted_dek: bytes, user_id: UUID) -> bytes:
        """
        Decrypt an encrypted DEK using the user's derived KEK.

        Expects input format: nonce (12 bytes) || ciphertext || tag

        Args:
            encrypted_dek: Encrypted DEK bytes (as returned by encrypt_dek)
            user_id: User UUID for per-user key derivation

        Returns:
            Raw DEK bytes

        Raises:
            ValueError: If encrypted_dek is empty or too short
            LocalKEKProviderError: If decryption fails (wrong key, corrupted data)
        """
        if not encrypted_dek:
            raise ValueError("Encrypted DEK cannot be empty")

        # Minimum length: nonce (12) + ciphertext (1) + tag (16) = 29 bytes
        min_length = self.NONCE_LENGTH + 1 + 16
        if len(encrypted_dek) < min_length:
            raise ValueError(
                f"Encrypted DEK too short: {len(encrypted_dek)} bytes, "
                f"minimum {min_length} bytes"
            )

        try:
            kek = self._derive_kek(user_id)
            aesgcm = AESGCM(kek)

            # Extract nonce and ciphertext
            nonce = encrypted_dek[: self.NONCE_LENGTH]
            ciphertext = encrypted_dek[self.NONCE_LENGTH :]

            # Decrypt and verify authentication tag
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)

            return plaintext

        except Exception as e:
            logger.error(
                "Failed to decrypt DEK",
                user_id=str(user_id),
                error=str(e),
            )
            raise LocalKEKProviderError(
                f"DEK decryption failed - key may be corrupted or "
                f"encryption key changed: {e}"
            ) from e

    def get_provider_version(self) -> str:
        """Return the provider version string."""
        return self.VERSION
