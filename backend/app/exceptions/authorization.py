"""
ExamShield - Authorization Exceptions

Custom exception classes for authorization-related errors.
"""

from typing import Any, Dict, List, Optional

from fastapi import status

from app.exceptions.api_exception import APIException


class InsufficientPermissionsException(APIException):
    """Raised when a user lacks the required permissions."""

    def __init__(
        self,
        message: str = "Insufficient permissions to perform this action",
        required_permissions: Optional[List[str]] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        if required_permissions and not errors:
            errors = [
                {
                    "field": "permissions",
                    "message": f"Missing permissions: {', '.join(required_permissions)}",
                    "type": "authorization_error",
                }
            ]
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            errors=errors,
        )


class RoleNotFoundException(APIException):
    """Raised when a requested role does not exist."""

    def __init__(
        self,
        message: str = "Role not found",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            errors=errors,
        )


class RoleAssignmentException(APIException):
    """Raised when a role assignment operation fails."""

    def __init__(
        self,
        message: str = "Role assignment failed",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=errors,
        )
