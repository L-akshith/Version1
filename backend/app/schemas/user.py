"""
ExamShield - User Schemas

Pydantic v2 schemas for user-related request/response payloads.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user (admin endpoint)."""

    email: EmailStr = Field(
        ...,
        description="User's email address",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User's password",
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name",
    )
    role_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Role ID to assign",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the account is active",
    )


class UserUpdate(BaseModel):
    """Schema for updating a user's profile."""

    email: Optional[EmailStr] = Field(
        default=None,
        description="New email address",
    )
    full_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="New full name",
    )
    password: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="New password",
    )
    is_active: Optional[bool] = Field(
        default=None,
        description="Active status",
    )


class UserResponse(BaseModel):
    """Schema for user response data."""

    id: uuid.UUID = Field(..., description="User UUID")
    email: str = Field(..., description="Email address")
    full_name: str = Field(..., description="Full name")
    is_active: bool = Field(..., description="Active status")
    is_superuser: bool = Field(..., description="Superuser status")
    role_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Assigned role UUID",
    )
    role_name: Optional[str] = Field(
        default=None,
        description="Assigned role name",
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class AssignRoleRequest(BaseModel):
    """Schema for assigning a role to a user."""

    role_id: uuid.UUID = Field(
        ...,
        description="The UUID of the role to assign",
    )
