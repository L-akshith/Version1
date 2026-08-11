import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


class AESGCMEncryptionService:
    """
    Provides AES-256-GCM authenticated encryption.

    AES-256 requires a 32-byte key.
    GCM nonce must be unique for every encryption operation.
    """

    KEY_SIZE = 32
    NONCE_SIZE = 12

    @staticmethod
    def generate_key() -> bytes:
        """Generate a cryptographically secure 256-bit AES key."""
        return AESGCM.generate_key(bit_length=256)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generate a cryptographically secure 96-bit GCM nonce."""
        return os.urandom(AESGCMEncryptionService.NONCE_SIZE)

    @staticmethod
    def encrypt(
        plaintext: bytes,
        key: bytes,
        associated_data: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """
        Encrypt plaintext using AES-256-GCM.

        Returns:
            ciphertext_with_tag, nonce
        """

        if len(key) != AESGCMEncryptionService.KEY_SIZE:
            raise ValueError("AES-256 key must be exactly 32 bytes.")

        if not isinstance(plaintext, bytes):
            raise TypeError("Plaintext must be bytes.")

        nonce = AESGCMEncryptionService.generate_nonce()

        aesgcm = AESGCM(key)

        ciphertext = aesgcm.encrypt(
            nonce,
            plaintext,
            associated_data,
        )

        return ciphertext, nonce

    @staticmethod
    def decrypt(
        ciphertext: bytes,
        key: bytes,
        nonce: bytes,
        associated_data: bytes | None = None,
    ) -> bytes:
        """
        Decrypt and authenticate AES-256-GCM ciphertext.
        """

        if len(key) != AESGCMEncryptionService.KEY_SIZE:
            raise ValueError("AES-256 key must be exactly 32 bytes.")

        if len(nonce) != AESGCMEncryptionService.NONCE_SIZE:
            raise ValueError("GCM nonce must be exactly 12 bytes.")

        aesgcm = AESGCM(key)

        try:
            return aesgcm.decrypt(
                nonce,
                ciphertext,
                associated_data,
            )
        except InvalidTag as exc:
            raise ValueError(
                "Authentication failed: ciphertext or associated data was modified."
            ) from exc
            
            # backend/tests/security/test_aes_gcm.py