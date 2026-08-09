"""
ExamShield - Security Module

Stub module providing interface contracts for future cryptography integration.
When cryptographic features (AES-256, RSA/ECC, digital signatures, etc.) are
implemented, they will be plugged into this module without changing the rest
of the application.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class EncryptionProvider(ABC):
    """
    Abstract encryption provider interface.

    Future implementations will provide:
    - AES-256 symmetric encryption
    - RSA/ECC key wrapping
    - Hybrid encryption schemes
    """

    @abstractmethod
    async def encrypt(self, plaintext: bytes, key_id: Optional[str] = None) -> bytes:
        """Encrypt plaintext data."""
        ...

    @abstractmethod
    async def decrypt(self, ciphertext: bytes, key_id: Optional[str] = None) -> bytes:
        """Decrypt ciphertext data."""
        ...


class SignatureProvider(ABC):
    """
    Abstract digital signature provider interface.

    Future implementations will provide:
    - RSA/ECDSA digital signatures
    - Signature verification
    - Certificate chain validation
    """

    @abstractmethod
    async def sign(self, data: bytes, key_id: str) -> bytes:
        """Create a digital signature for the given data."""
        ...

    @abstractmethod
    async def verify(self, data: bytes, signature: bytes, key_id: str) -> bool:
        """Verify a digital signature."""
        ...


class WatermarkProvider(ABC):
    """
    Abstract forensic watermarking provider interface.

    Future implementations will provide:
    - Invisible forensic watermarking
    - Watermark extraction
    - Watermark verification
    """

    @abstractmethod
    async def embed(self, document: bytes, watermark_data: dict[str, Any]) -> bytes:
        """Embed an invisible watermark into a document."""
        ...

    @abstractmethod
    async def extract(self, document: bytes) -> Optional[dict[str, Any]]:
        """Extract watermark data from a document."""
        ...


class KeyManager(ABC):
    """
    Abstract key management interface.

    Future implementations will provide:
    - Key generation and rotation
    - Key wrapping/unwrapping
    - Key storage and retrieval
    - Hardware Security Module (HSM) integration
    """

    @abstractmethod
    async def generate_key(self, key_type: str, key_size: int) -> str:
        """Generate a new cryptographic key and return its ID."""
        ...

    @abstractmethod
    async def get_key(self, key_id: str) -> bytes:
        """Retrieve a cryptographic key by its ID."""
        ...

    @abstractmethod
    async def rotate_key(self, key_id: str) -> str:
        """Rotate a key and return the new key ID."""
        ...

    @abstractmethod
    async def wrap_key(self, key_to_wrap: bytes, wrapping_key_id: str) -> bytes:
        """Wrap (encrypt) a key using another key."""
        ...

    @abstractmethod
    async def unwrap_key(self, wrapped_key: bytes, wrapping_key_id: str) -> bytes:
        """Unwrap (decrypt) a key using another key."""
        ...


class NoOpEncryptionProvider(EncryptionProvider):
    """Pass-through encryption provider used until real cryptography is plugged in."""

    async def encrypt(self, plaintext: bytes, key_id: Optional[str] = None) -> bytes:
        return plaintext

    async def decrypt(self, ciphertext: bytes, key_id: Optional[str] = None) -> bytes:
        return ciphertext


class NoOpSignatureProvider(SignatureProvider):
    """Pass-through signature provider used until real cryptography is plugged in."""

    async def sign(self, data: bytes, key_id: str) -> bytes:
        return b"no-op-signature"

    async def verify(self, data: bytes, signature: bytes, key_id: str) -> bool:
        return True


class NoOpWatermarkProvider(WatermarkProvider):
    """Pass-through watermark provider used until real cryptography is plugged in."""

    async def embed(self, document: bytes, watermark_data: dict[str, Any]) -> bytes:
        return document

    async def extract(self, document: bytes) -> Optional[dict[str, Any]]:
        return None


# ── Module-Level Singletons ──────────────────────────────────────
# These are the active providers. Replace with real implementations
# when cryptography features are integrated.

_encryption_provider: EncryptionProvider = NoOpEncryptionProvider()
_signature_provider: SignatureProvider = NoOpSignatureProvider()
_watermark_provider: WatermarkProvider = NoOpWatermarkProvider()


def get_encryption_provider() -> EncryptionProvider:
    """Return the active encryption provider."""
    return _encryption_provider


def set_encryption_provider(provider: EncryptionProvider) -> None:
    """Replace the active encryption provider."""
    global _encryption_provider
    _encryption_provider = provider


def get_signature_provider() -> SignatureProvider:
    """Return the active signature provider."""
    return _signature_provider


def set_signature_provider(provider: SignatureProvider) -> None:
    """Replace the active signature provider."""
    global _signature_provider
    _signature_provider = provider


def get_watermark_provider() -> WatermarkProvider:
    """Return the active watermark provider."""
    return _watermark_provider


def set_watermark_provider(provider: WatermarkProvider) -> None:
    """Replace the active watermark provider."""
    global _watermark_provider
    _watermark_provider = provider
