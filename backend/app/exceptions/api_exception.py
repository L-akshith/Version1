"""
ExamShield - Base API Exception

Provides the base exception class and global exception handler registration
for consistent error responses across the entire application.
"""

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException


class APIException(Exception):
    """
    Base exception class for all application-specific exceptions.

    All custom exceptions should inherit from this class to ensure
    consistent error response formatting.
    """

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.message = message
        self.status_code = status_code
        self.errors = errors or []
        super().__init__(self.message)


class NotFoundException(APIException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            errors=errors,
        )


class ConflictException(APIException):
    """Raised when a resource conflict occurs (e.g., duplicate email)."""

    def __init__(
        self,
        message: str = "Resource conflict",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            errors=errors,
        )


class BadRequestException(APIException):
    """Raised when the request is malformed or invalid."""

    def __init__(
        self,
        message: str = "Bad request",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            errors=errors,
        )


class ForbiddenException(APIException):
    """Raised when the user is authenticated but not authorized to perform the action."""

    def __init__(
        self,
        message: str = "Forbidden",
        errors: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            errors=errors,
        )


def _build_error_response(
    success: bool,
    message: str,
    status_code: int,
    errors: Optional[List[Dict[str, Any]]] = None,
) -> JSONResponse:
    """Build a standardized JSON error response."""
    return JSONResponse(
        status_code=status_code,
        content={
            "success": success,
            "message": message,
            "data": None,
            "errors": errors or [],
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI application."""

    @app.exception_handler(APIException)
    async def api_exception_handler(
        request: Request, exc: APIException
    ) -> JSONResponse:
        return _build_error_response(
            success=False,
            message=exc.message,
            status_code=exc.status_code,
            errors=exc.errors,
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return _build_error_response(
            success=False,
            message=str(exc.detail),
            status_code=exc.status_code,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        errors = []
        for error in exc.errors():
            errors.append(
                {
                    "field": " -> ".join(str(loc) for loc in error.get("loc", [])),
                    "message": error.get("msg", "Validation error"),
                    "type": error.get("type", "value_error"),
                }
            )
        return _build_error_response(
            success=False,
            message="Validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        import logging

        logger = logging.getLogger("examshield")
        logger.exception(f"Unhandled exception: {exc}")
        return _build_error_response(
            success=False,
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
