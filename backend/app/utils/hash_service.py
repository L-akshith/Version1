"""
ExamShield - Hash Service

Provides cryptographic hash generation for file integrity verification.
Currently supports SHA-256; designed for future algorithm extensibility.
"""

import hashlib
import logging

logger = logging.getLogger("examshield.hash_service")


class HashService:
    """
    Cryptographic hash generation service.

    Generates file integrity hashes using industry-standard algorithms.
    SHA-256 is the default; additional algorithms can be added as needed.
    """

    @staticmethod
    def generate_sha256(data: bytes) -> str:
        """
        Generate a SHA-256 hexadecimal hash of the given data.

        Args:
            data: Raw bytes to hash.

        Returns:
            Lowercase hexadecimal SHA-256 digest string (64 characters).
        """
        digest = hashlib.sha256(data).hexdigest()
        logger.debug("SHA-256 hash generated: %s...%s", digest[:8], digest[-8:])
        return digest

    @staticmethod
    def verify_sha256(data: bytes, expected_hash: str) -> bool:
        """
        Verify that the SHA-256 hash of data matches the expected hash.

        Args:
            data: Raw bytes to verify.
            expected_hash: Expected hexadecimal SHA-256 digest.

        Returns:
            True if the computed hash matches the expected hash.
        """
        computed = hashlib.sha256(data).hexdigest()
        return computed == expected_hash.lower()
