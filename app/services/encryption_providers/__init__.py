"""
Encryption providers package.

Provides Key Encryption Key (KEK) providers for envelope encryption.
Each provider implements the KEKProvider ABC for encrypting/decrypting DEKs.

Available providers:
- LocalKEKProvider: Uses local master key with PBKDF2 key derivation
- (Future) AWSKMSProvider: Uses AWS KMS for key management
"""

from app.services.encryption_providers.base import KEKProvider
from app.services.encryption_providers.local_kek import LocalKEKProvider

__all__ = ["KEKProvider", "LocalKEKProvider"]
