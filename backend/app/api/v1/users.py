"""
ExamShield - User Management API Routes

CRUD endpoints for user management with role-based access control.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    require_permissions,
    get_async_session,
)
from app.database.session import get_async_session
from app.schemas.response import APIResponse, PaginatedResponse
from app.schemas.user import AssignRoleRequest, UserResponse, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["User Management"])


@router.get(
    "",
    response_model=PaginatedResponse[UserResponse],
    summary="List all users",
    description="Retrieve a paginated list of all users. Requires 'users:list' permission.",
    dependencies=[Depends(require_permissions(["users:list"]))],
)
async def list_users(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
) -> PaginatedResponse[UserResponse]:
    """List all users with pagination."""
    service = UserService(session)
    users = await service.list_users(skip=skip, limit=limit)
    total = await service.get_user_count()
    return PaginatedResponse(
        data=users,
        total=total,
        skip=skip,
        limit=limit,
        message="Users retrieved successfully",
    )


@router.get(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    summary="Get user by ID",
    description="Retrieve a specific user by their UUID. Requires 'users:read' permission.",
    dependencies=[Depends(require_permissions(["users:read"]))],
)
async def get_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Get a single user by ID."""
    service = UserService(session)
    user = await service.get_user(user_id)
    return APIResponse.ok(data=user, message="User retrieved successfully")


@router.put(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    summary="Update user",
    description="Update a user's profile information. Requires 'users:update' permission.",
    dependencies=[Depends(require_permissions(["users:update"]))],
)
async def update_user(
    user_id: uuid.UUID,
    update_data: UserUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Update a user's profile."""
    service = UserService(session)
    user = await service.update_user(user_id, update_data)
    return APIResponse.ok(data=user, message="User updated successfully")


@router.delete(
    "/{user_id}",
    response_model=APIResponse[None],
    summary="Delete user",
    description="Delete a user by their UUID. Requires 'users:delete' permission.",
    dependencies=[Depends(require_permissions(["users:delete"]))],
)
async def delete_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[None]:
    """Delete a user."""
    service = UserService(session)
    await service.delete_user(user_id)
    return APIResponse.ok(message="User deleted successfully")


@router.put(
    "/{user_id}/role",
    response_model=APIResponse[UserResponse],
    summary="Assign role to user",
    description="Assign a new role to a user. Requires 'users:manage' permission.",
    dependencies=[Depends(require_permissions(["users:manage"]))],
)
async def assign_role(
    user_id: uuid.UUID,
    request: AssignRoleRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Assign a role to a user."""
    service = UserService(session)
    user = await service.assign_role(user_id, request.role_id)
    return APIResponse.ok(data=user, message="Role assigned successfully")


@router.put(
    "/{user_id}/deactivate",
    response_model=APIResponse[UserResponse],
    summary="Deactivate user",
    description="Deactivate a user account. Requires 'users:manage' permission.",
    dependencies=[Depends(require_permissions(["users:manage"]))],
)
async def deactivate_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Deactivate a user account."""
    service = UserService(session)
    user = await service.deactivate_user(user_id)
    return APIResponse.ok(data=user, message="User deactivated successfully")


@router.put(
    "/{user_id}/activate",
    response_model=APIResponse[UserResponse],
    summary="Activate user",
    description="Activate a user account. Requires 'users:manage' permission.",
    dependencies=[Depends(require_permissions(["users:manage"]))],
)
async def activate_user(
    user_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[UserResponse]:
    """Activate a user account."""
    service = UserService(session)
    user = await service.activate_user(user_id)
    return APIResponse.ok(data=user, message="User activated successfully")
