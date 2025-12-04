"""
Abstract base class for Key Encryption Key (KEK) providers.

KEK providers are responsible for encrypting and decrypting Data Encryption Keys (DEKs)
as part of the envelope encryption pattern.

The envelope encryption pattern:
1. Each piece of sensitive data gets its own DEK (Data Encryption Key)
2. The DEK encrypts the actual data
3. The KEK (Key Encryption Key) encrypts the DEK
4. Only the encrypted DEK is stored in the database

Benefits:
- Per-record encryption isolation
- GDPR-compliant deletion (destroy DEK = data unrecoverable)
- Easy key rotation (re-encrypt DEKs with new KEK)
- Future-proof for KMS migration (swap provider without re-encrypting data)
"""

from abc import ABC, abstractmethod
from uuid import UUID


class KEKProvider(ABC):
    """
    Abstract base class for Key Encryption Key providers.

    Implementations must provide methods to encrypt and decrypt DEKs
    using a per-user KEK. The KEK itself may be:
    - Derived from a master key (LocalKEKProvider)
    - Managed by a cloud KMS (future AWSKMSProvider, GCPKMSProvider)

    Thread Safety:
        Implementations should be thread-safe for concurrent use.

    Example:
        >>> provider = LocalKEKProvider(master_key="...")
        >>> dek = os.urandom(32)  # Generate random DEK
        >>> encrypted_dek = await provider.encrypt_dek(dek, user_id)
        >>> # Store encrypted_dek in database
        >>> decrypted_dek = await provider.decrypt_dek(encrypted_dek, user_id)
        >>> assert dek == decrypted_dek
    """

    @abstractmethod
    async def encrypt_dek(self, dek: bytes, user_id: UUID) -> bytes:
        """
        Encrypt a Data Encryption Key using the user's KEK.

        Args:
            dek: Raw Data Encryption Key bytes (typically 32 bytes for AES-256)
            user_id: User UUID for per-user key isolation

        Returns:
            Encrypted DEK bytes (includes any necessary metadata like nonce)

        Raises:
            ValueError: If dek is empty or invalid
            EncryptionError: If encryption fails
        """
        pass

    @abstractmethod
    async def decrypt_dek(self, encrypted_dek: bytes, user_id: UUID) -> bytes:
        """
        Decrypt an encrypted Data Encryption Key.

        Args:
            encrypted_dek: Encrypted DEK bytes (as returned by encrypt_dek)
            user_id: User UUID for per-user key isolation

        Returns:
            Raw DEK bytes

        Raises:
            ValueError: If encrypted_dek is empty or invalid
            DecryptionError: If decryption fails (wrong key, corrupted data)
        """
        pass

    @abstractmethod
    def get_provider_version(self) -> str:
        """
        Get the version identifier for this KEK provider.

        The version string is stored with each DEK record to ensure
        the correct provider is used for decryption. This enables:
        - Migration between providers (local -> KMS)
        - Versioning within a provider (algorithm changes)

        Returns:
            Version string (e.g., "local-v1", "aws-kms-v1")

        Example versions:
            - "local-v1": Local master key with AES-GCM
            - "aws-kms-v1": AWS KMS managed keys
            - "gcp-kms-v1": GCP KMS managed keys
        """
        pass

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} version={self.get_provider_version()}>"
