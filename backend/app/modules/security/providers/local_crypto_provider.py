"""
ExamShield - Local Development Cryptographic Provider

Development-only cryptographic provider.

RSA private keys are held in process memory.
They are NOT persisted and must NOT be used in production.
"""

from typing import Dict

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.modules.security.interfaces.crypto_key_provider import (
    CryptoKeyProvider,
)


class LocalCryptoKeyProvider(CryptoKeyProvider):

    def __init__(self) -> None:
        self._private_keys: Dict[str, rsa.RSAPrivateKey] = {}

    async def generate_rsa_key(
        self,
        key_identifier: str,
    ) -> None:

        if key_identifier in self._private_keys:
            raise ValueError(
                f"Cryptographic key '{key_identifier}' already exists."
            )

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        self._private_keys[key_identifier] = private_key

    async def get_public_key(
        self,
        key_identifier: str,
    ):
        private_key = self._get_private_key(key_identifier)
        return private_key.public_key()

    async def wrap_key(
        self,
        key_identifier: str,
        plaintext_key: bytes,
    ) -> bytes:

        if not plaintext_key:
            raise ValueError("Plaintext key cannot be empty.")

        public_key = await self.get_public_key(
            key_identifier
        )

        return public_key.encrypt(
            plaintext_key,
            padding.OAEP(
                mgf=padding.MGF1(
                    algorithm=hashes.SHA256()
                ),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    async def unwrap_key(
        self,
        key_identifier: str,
        wrapped_key: bytes,
    ) -> bytes:

        if not wrapped_key:
            raise ValueError("Wrapped key cannot be empty.")

        private_key = self._get_private_key(
            key_identifier
        )

        return private_key.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(
                    algorithm=hashes.SHA256()
                ),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    def _get_private_key(
        self,
        key_identifier: str,
    ) -> rsa.RSAPrivateKey:

        private_key = self._private_keys.get(
            key_identifier
        )

        if private_key is None:
            raise KeyError(
                f"Cryptographic key '{key_identifier}' not found."
            )

        return private_key