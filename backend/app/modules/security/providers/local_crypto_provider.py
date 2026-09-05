"""
ExamShield - Local Development Cryptographic Provider

Development-only cryptographic provider with file-based persistence.

RSA private keys are persisted as PEM files under .local_keys/ so they
survive backend restarts during local development.

MUST NOT be used in production — use a real KMS instead.
"""

import logging
from pathlib import Path
from typing import Dict

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.modules.security.interfaces.crypto_key_provider import (
    CryptoKeyProvider,
)

logger = logging.getLogger("examshield.local_crypto_provider")

# Default directory for persisted dev keys, relative to the working directory.
_DEFAULT_KEY_DIR = Path(__file__).resolve().parents[4] / ".local_keys"


class LocalCryptoKeyProvider(CryptoKeyProvider):
    """
    Development-only CryptoKeyProvider that persists RSA private keys as
    PEM files on disk so they survive process restarts.
    """

    def __init__(self, key_dir: Path | None = None) -> None:
        self._key_dir = key_dir or _DEFAULT_KEY_DIR
        self._key_dir.mkdir(parents=True, exist_ok=True)
        self._private_keys: Dict[str, rsa.RSAPrivateKey] = {}
        self._load_existing_keys()

    # ── Key generation ───────────────────────────────────────────

    async def generate_rsa_key(
        self,
        key_identifier: str,
    ) -> None:
        if key_identifier in self._private_keys:
            raise ValueError(
                f"Cryptographic key '{key_identifier}' already exists."
            )

        pem_path = self._pem_path(key_identifier)
        if pem_path.exists():
            raise ValueError(
                f"Cryptographic key '{key_identifier}' already exists on disk."
            )

        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=4096,
        )

        self._save_private_key(key_identifier, private_key)
        self._private_keys[key_identifier] = private_key
        logger.info("Generated and persisted RSA key '%s'.", key_identifier)

    # ── Public key retrieval ─────────────────────────────────────

    async def get_public_key(
        self,
        key_identifier: str,
    ):
        private_key = self._get_private_key(key_identifier)
        return private_key.public_key()

    # ── Key wrapping (RSA-OAEP SHA-256) ──────────────────────────

    async def wrap_key(
        self,
        key_identifier: str,
        plaintext_key: bytes,
    ) -> bytes:
        if not plaintext_key:
            raise ValueError("Plaintext key cannot be empty.")

        public_key = await self.get_public_key(key_identifier)

        return public_key.encrypt(
            plaintext_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    # ── Key unwrapping (RSA-OAEP SHA-256) ────────────────────────

    async def unwrap_key(
        self,
        key_identifier: str,
        wrapped_key: bytes,
    ) -> bytes:
        if not wrapped_key:
            raise ValueError("Wrapped key cannot be empty.")

        private_key = self._get_private_key(key_identifier)

        return private_key.decrypt(
            wrapped_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )

    # ── Private helpers ──────────────────────────────────────────

    def _pem_path(self, key_identifier: str) -> Path:
        """Return the PEM file path for a given key identifier."""
        safe_name = key_identifier.replace("/", "_").replace("\\", "_")
        return self._key_dir / f"{safe_name}.pem"

    def _save_private_key(
        self, key_identifier: str, private_key: rsa.RSAPrivateKey
    ) -> None:
        """Persist a private key as an unencrypted PEM file (dev only)."""
        pem_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        pem_path = self._pem_path(key_identifier)
        pem_path.write_bytes(pem_bytes)

    def _load_existing_keys(self) -> None:
        """Load all existing PEM files from the key directory into memory."""
        if not self._key_dir.exists():
            return

        for pem_file in self._key_dir.glob("*.pem"):
            key_identifier = pem_file.stem
            try:
                pem_bytes = pem_file.read_bytes()
                private_key = serialization.load_pem_private_key(
                    pem_bytes, password=None
                )
                if isinstance(private_key, rsa.RSAPrivateKey):
                    self._private_keys[key_identifier] = private_key
                    logger.debug(
                        "Loaded persisted RSA key '%s'.", key_identifier
                    )
                else:
                    logger.warning(
                        "Skipping non-RSA key file: %s", pem_file.name
                    )
            except Exception:
                logger.warning(
                    "Failed to load key from '%s', skipping.", pem_file.name,
                    exc_info=True,
                )

    def _get_private_key(
        self,
        key_identifier: str,
    ) -> rsa.RSAPrivateKey:
        """
        Look up a private key by identifier.

        Checks the in-memory cache first, then falls back to disk.
        Never silently generates a replacement key.
        """
        private_key = self._private_keys.get(key_identifier)

        if private_key is not None:
            return private_key

        # Attempt disk fallback (e.g. key was loaded by another instance)
        pem_path = self._pem_path(key_identifier)
        if pem_path.exists():
            try:
                pem_bytes = pem_path.read_bytes()
                loaded_key = serialization.load_pem_private_key(
                    pem_bytes, password=None
                )
                if isinstance(loaded_key, rsa.RSAPrivateKey):
                    self._private_keys[key_identifier] = loaded_key
                    return loaded_key
            except Exception:
                pass

        raise KeyError(
            f"Cryptographic key '{key_identifier}' not found. "
            f"The key may have been generated in a previous session that "
            f"did not persist keys, or the .local_keys/ directory was deleted."
        )

    async def validate_key_availability(
        self,
        key_identifier: str,
    ) -> bool:
        """
        Check if the specified key exists locally.
        """
        try:
            self._get_private_key(key_identifier)
            return True
        except KeyError:
            return False