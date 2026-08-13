from dataclasses import dataclass

from app.modules.security.encryption.aes_gcm import (
    AESGCMEncryptionService,
)
from app.modules.security.encryption.rsa_oaep import (
    RSAOAEPKeyWrapper,
)


@dataclass(frozen=True)
class EncryptedPackage:
    ciphertext: bytes
    nonce: bytes
    wrapped_aes_key: bytes


class HybridEncryptionService:
    """
    Hybrid encryption for ExamShield question papers.

    AES-256-GCM encrypts the actual document.
    RSA-4096-OAEP protects the randomly generated AES key.
    """

    @staticmethod
    def encrypt(
        plaintext: bytes,
        rsa_public_key,
        associated_data: bytes | None = None,
    ) -> EncryptedPackage:

        if not plaintext:
            raise ValueError("Plaintext cannot be empty.")

        # Generate a unique AES-256 session key for this encryption.
        aes_key = AESGCMEncryptionService.generate_key()

        # Encrypt the actual document.
        ciphertext, nonce = AESGCMEncryptionService.encrypt(
            plaintext=plaintext,
            key=aes_key,
            associated_data=associated_data,
        )

        # Protect the AES session key with RSA-OAEP.
        wrapped_aes_key = RSAOAEPKeyWrapper.wrap_key(
            aes_key=aes_key,
            public_key=rsa_public_key,
        )

        return EncryptedPackage(
            ciphertext=ciphertext,
            nonce=nonce,
            wrapped_aes_key=wrapped_aes_key,
        )

    @staticmethod
    def decrypt(
        package: EncryptedPackage,
        rsa_private_key,
        associated_data: bytes | None = None,
    ) -> bytes:

        # Recover the AES session key.
        aes_key = RSAOAEPKeyWrapper.unwrap_key(
            wrapped_key=package.wrapped_aes_key,
            private_key=rsa_private_key,
        )

        # Decrypt and authenticate the document.
        return AESGCMEncryptionService.decrypt(
            ciphertext=package.ciphertext,
            key=aes_key,
            nonce=package.nonce,
            associated_data=associated_data,
        )