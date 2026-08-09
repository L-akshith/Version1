"""
ExamShield - Generic API Response Schema

Provides a standardized response envelope for all API endpoints.
"""

from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class APIResponse(BaseModel, Generic[DataT]):
    """
    Generic API response wrapper.

    All API endpoints return this structure for consistency:
    {
        "success": true/false,
        "message": "Human-readable message",
        "data": <payload>,
        "errors": [<error objects>]
    }
    """

    success: bool = Field(
        default=True,
        description="Whether the request was successful",
    )
    message: str = Field(
        default="Success",
        description="Human-readable response message",
    )
    data: Optional[DataT] = Field(
        default=None,
        description="Response payload",
    )
    errors: List[Any] = Field(
        default_factory=list,
        description="List of error details if the request failed",
    )

    model_config = {"from_attributes": True}

    @classmethod
    def ok(
        cls,
        data: Optional[DataT] = None,
        message: str = "Success",
    ) -> "APIResponse[DataT]":
        """Create a successful response."""
        return cls(success=True, message=message, data=data, errors=[])

    @classmethod
    def error(
        cls,
        message: str = "An error occurred",
        errors: Optional[List[Any]] = None,
    ) -> "APIResponse[None]":
        """Create an error response."""
        return cls(
            success=False,
            message=message,
            data=None,
            errors=errors or [],
        )


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Paginated response wrapper for list endpoints."""

    success: bool = True
    message: str = "Success"
    data: List[DataT] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 100
    errors: List[Any] = Field(default_factory=list)

    model_config = {"from_attributes": True}
