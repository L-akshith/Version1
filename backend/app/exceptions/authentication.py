"""
ExamShield - Authentication Exceptions

Custom exception classes for authentication-related errors.
"""

from typing import Any, Dict, List, Optional

from fastapi import status

from app.exceptions.api_exception import APIException


class InvalidCredentialsException(APIException):
    """Raised when login credentials are invalid."""

    def __init__(
        self,
        message: str = "Invalid email or password",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            errors=errors,
        )


class TokenExpiredException(APIException):
    """Raised when a JWT token has expired."""

    def __init__(
        self,
        message: str = "Token has expired",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            errors=errors,
        )


class InvalidTokenException(APIException):
    """Raised when a JWT token is malformed or invalid."""

    def __init__(
        self,
        message: str = "Invalid or malformed token",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            errors=errors,
        )


class InactiveUserException(APIException):
    """Raised when a deactivated user attempts to authenticate."""

    def __init__(
        self,
        message: str = "User account is deactivated",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            errors=errors,
        )
