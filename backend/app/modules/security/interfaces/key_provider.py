"""
ExamShield - Key Provider Interface

Abstract base class for integrating with various Key Management Systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List

from app.models.key_metadata import KeyMetadata, Algorithm, KeyPurpose


class KeyProvider(ABC):
    """
    Interface for integrating with external KMS (AWS KMS, Azure Key Vault, etc.)
    or local development providers.
    
    This provider should NEVER return raw symmetric private key material,
    only identifiers and metadata.
    """

    @abstractmethod
    async def generate_key_metadata(
        self, algorithm: Algorithm, purpose: KeyPurpose, created_by: str
    ) -> KeyMetadata:
        """
        Generate a new key in the underlying KMS and return its metadata representation.
        """
        pass

    @abstractmethod
    async def rotate_key(self, current_key_identifier: str) -> KeyMetadata:
        """
        Rotate an existing key, generating a new version.
        """
        pass

    @abstractmethod
    async def activate_key(self, key_identifier: str) -> bool:
        """
        Activate a key in the KMS for cryptographic operations.
        """
        pass

    @abstractmethod
    async def deactivate_key(self, key_identifier: str) -> bool:
        """
        Deactivate (suspend) a key from cryptographic operations.
        """
        pass

    @abstractmethod
    async def list_active_keys(self) -> List[KeyMetadata]:
        """
        List all currently active keys from the provider.
        """
        pass

    @abstractmethod
    async def get_key_metadata(self, key_identifier: str) -> KeyMetadata:
        """
        Retrieve metadata for a specific key identifier.
        """
        pass
