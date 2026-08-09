"""
ExamShield - JWT Utilities

Provides JWT token creation and decoding using python-jose.
Supports both access tokens and refresh tokens.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()


def create_access_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: The token subject (typically user ID as string).
        extra_claims: Additional claims to include in the token payload.

    Returns:
        Encoded JWT access token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "access",
        "jti": str(uuid.uuid4()),
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def create_refresh_token(
    subject: str,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: The token subject (typically user ID as string).
        extra_claims: Additional claims to include in the token payload.

    Returns:
        Encoded JWT refresh token string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=settings.JWT_REFRESH_TOKEN_EXPIRE_MINUTES)

    payload: Dict[str, Any] = {
        "sub": str(subject),
        "iat": now,
        "exp": expire,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
    }

    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded token payload as a dictionary.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


def decode_token_safe(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode a JWT token without raising exceptions.

    Args:
        token: The JWT token string to decode.

    Returns:
        The decoded payload if valid, None otherwise.
    """
    try:
        return decode_token(token)
    except JWTError:
        return None
