"""
ExamShield - Role Schemas

Pydantic v2 schemas for role and permission management payloads.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PermissionResponse(BaseModel):
    """Schema for permission response data."""

    id: uuid.UUID = Field(..., description="Permission UUID")
    name: str = Field(..., description="Permission name (resource:action)")
    description: str = Field(default="", description="Permission description")
    resource: str = Field(..., description="Resource name")
    action: str = Field(..., description="Action name")

    model_config = {"from_attributes": True}


class RoleCreate(BaseModel):
    """Schema for creating a new role."""

    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Role name (must be unique)",
        examples=["Paper Coordinator"],
    )
    description: str = Field(
        default="",
        max_length=500,
        description="Role description",
    )
    permission_ids: List[uuid.UUID] = Field(
        default_factory=list,
        description="List of permission UUIDs to assign to this role",
    )


class RoleUpdate(BaseModel):
    """Schema for updating a role."""

    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
        description="New role name",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=500,
        description="New role description",
    )


class RoleResponse(BaseModel):
    """Schema for role response data."""

    id: uuid.UUID = Field(..., description="Role UUID")
    name: str = Field(..., description="Role name")
    description: str = Field(default="", description="Role description")
    permissions: List[PermissionResponse] = Field(
        default_factory=list,
        description="Permissions assigned to this role",
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class AddPermissionRequest(BaseModel):
    """Schema for adding a permission to a role."""

    permission_id: uuid.UUID = Field(
        ...,
        description="The UUID of the permission to add",
    )
