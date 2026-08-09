"""
ExamShield - Password Utilities

Provides password hashing and verification using bcrypt
via the passlib library.
"""

from passlib.context import CryptContext

_pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
)


def hash_password(plain_password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args:
        plain_password: The plaintext password to hash.

    Returns:
        The bcrypt-hashed password string.
    """
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args:
        plain_password: The plaintext password to check.
        hashed_password: The stored bcrypt hash to verify against.

    Returns:
        True if the password matches, False otherwise.
    """
    return _pwd_context.verify(plain_password, hashed_password)
