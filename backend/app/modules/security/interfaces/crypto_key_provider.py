"""
ExamShield - Cryptographic Key Provider Interface

Provides controlled access to cryptographic operations involving
asymmetric keys.

This interface is separate from KeyProvider because KeyProvider
manages key lifecycle metadata, while this interface performs
cryptographic operations.
"""

from abc import ABC, abstractmethod


class CryptoKeyProvider(ABC):

    @abstractmethod
    async def get_public_key(self, key_identifier: str):
        """
        Return the public key associated with a key identifier.

        Public key material may be used internally for encryption.
        """
        pass

    @abstractmethod
    async def wrap_key(
        self,
        key_identifier: str,
        plaintext_key: bytes,
    ) -> bytes:
        """
        Wrap a symmetric key using the asymmetric key identified
        by key_identifier.
        """
        pass

    @abstractmethod
    async def unwrap_key(
        self,
        key_identifier: str,
        wrapped_key: bytes,
    ) -> bytes:
        """
        Unwrap a symmetric key internally.

        Raw private key material must never be exposed to callers.
        """
        pass
    
    @abstractmethod
    async def generate_rsa_key(
        self,
        key_identifier: str,
    ) -> None:
        pass