"""
ExamShield - Role Management API Routes

CRUD endpoints for role and permission management with RBAC.
"""

import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions, get_async_session
from app.database.session import get_async_session
from app.exceptions.api_exception import ConflictException, NotFoundException
from app.models.permission import Permission
from app.repositories.role_repository import RoleRepository
from app.schemas.response import APIResponse, PaginatedResponse
from app.schemas.role import (
    AddPermissionRequest,
    PermissionResponse,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)

router = APIRouter(prefix="/roles", tags=["Role Management"])


@router.get(
    "",
    response_model=PaginatedResponse[RoleResponse],
    summary="List all roles",
    description="Retrieve a paginated list of all roles with their permissions.",
    dependencies=[Depends(require_permissions(["roles:list"]))],
)
async def list_roles(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> PaginatedResponse[RoleResponse]:
    """List all roles with pagination."""
    repo = RoleRepository(session)
    roles = await repo.get_all_with_permissions(skip=skip, limit=limit)
    total = await repo.count()

    role_responses = [
        RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description or "",
            permissions=[
                PermissionResponse(
                    id=p.id,
                    name=p.name,
                    description=p.description or "",
                    resource=p.resource,
                    action=p.action,
                )
                for p in role.permissions
            ],
            created_at=role.created_at,
            updated_at=role.updated_at,
        )
        for role in roles
    ]

    return PaginatedResponse(
        data=role_responses,
        total=total,
        skip=skip,
        limit=limit,
        message="Roles retrieved successfully",
    )


@router.post(
    "",
    response_model=APIResponse[RoleResponse],
    status_code=201,
    summary="Create a new role",
    description="Create a new role with optional permission assignments.",
    dependencies=[Depends(require_permissions(["roles:create"]))],
)
async def create_role(
    request: RoleCreate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[RoleResponse]:
    """Create a new role."""
    repo = RoleRepository(session)

    if await repo.name_exists(request.name):
        raise ConflictException(message=f"Role '{request.name}' already exists")

    role_data = {
        "name": request.name,
        "description": request.description,
    }
    role = await repo.create(role_data)

    # Assign permissions if provided
    for perm_id in request.permission_ids:
        await repo.add_permission(role.id, perm_id)

    role = await repo.get_with_permissions(role.id)

    response = RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                description=p.description or "",
                resource=p.resource,
                action=p.action,
            )
            for p in role.permissions
        ],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

    return APIResponse.ok(data=response, message="Role created successfully")


@router.get(
    "/{role_id}",
    response_model=APIResponse[RoleResponse],
    summary="Get role by ID",
    description="Retrieve a specific role with its permissions.",
    dependencies=[Depends(require_permissions(["roles:read"]))],
)
async def get_role(
    role_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[RoleResponse]:
    """Get a single role by ID."""
    repo = RoleRepository(session)
    role = await repo.get_with_permissions(role_id)

    if role is None:
        raise NotFoundException(message=f"Role with ID '{role_id}' not found")

    response = RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                description=p.description or "",
                resource=p.resource,
                action=p.action,
            )
            for p in role.permissions
        ],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

    return APIResponse.ok(data=response, message="Role retrieved successfully")


@router.put(
    "/{role_id}",
    response_model=APIResponse[RoleResponse],
    summary="Update role",
    description="Update a role's name and description.",
    dependencies=[Depends(require_permissions(["roles:update"]))],
)
async def update_role(
    role_id: uuid.UUID,
    update_data: RoleUpdate,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[RoleResponse]:
    """Update a role."""
    repo = RoleRepository(session)

    existing = await repo.get_by_id(role_id)
    if existing is None:
        raise NotFoundException(message=f"Role with ID '{role_id}' not found")

    data = update_data.model_dump(exclude_unset=True)
    if "name" in data and data["name"] != existing.name:
        if await repo.name_exists(data["name"]):
            raise ConflictException(message=f"Role '{data['name']}' already exists")

    if data:
        await repo.update(role_id, data)

    role = await repo.get_with_permissions(role_id)

    response = RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                description=p.description or "",
                resource=p.resource,
                action=p.action,
            )
            for p in role.permissions
        ],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

    return APIResponse.ok(data=response, message="Role updated successfully")


@router.delete(
    "/{role_id}",
    response_model=APIResponse[None],
    summary="Delete role",
    description="Delete a role. Users assigned this role will have their role set to NULL.",
    dependencies=[Depends(require_permissions(["roles:delete"]))],
)
async def delete_role(
    role_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[None]:
    """Delete a role."""
    repo = RoleRepository(session)

    if not await repo.exists(role_id):
        raise NotFoundException(message=f"Role with ID '{role_id}' not found")

    await repo.delete(role_id)
    return APIResponse.ok(message="Role deleted successfully")


@router.post(
    "/{role_id}/permissions",
    response_model=APIResponse[RoleResponse],
    summary="Add permission to role",
    description="Add a permission to a role.",
    dependencies=[Depends(require_permissions(["roles:manage"]))],
)
async def add_permission_to_role(
    role_id: uuid.UUID,
    request: AddPermissionRequest,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[RoleResponse]:
    """Add a permission to a role."""
    repo = RoleRepository(session)

    role = await repo.add_permission(role_id, request.permission_id)
    if role is None:
        raise NotFoundException(message="Role or permission not found")

    response = RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                description=p.description or "",
                resource=p.resource,
                action=p.action,
            )
            for p in role.permissions
        ],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

    return APIResponse.ok(data=response, message="Permission added to role")


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=APIResponse[RoleResponse],
    summary="Remove permission from role",
    description="Remove a permission from a role.",
    dependencies=[Depends(require_permissions(["roles:manage"]))],
)
async def remove_permission_from_role(
    role_id: uuid.UUID,
    permission_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[RoleResponse]:
    """Remove a permission from a role."""
    repo = RoleRepository(session)

    role = await repo.remove_permission(role_id, permission_id)
    if role is None:
        raise NotFoundException(message="Role not found")

    response = RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description or "",
        permissions=[
            PermissionResponse(
                id=p.id,
                name=p.name,
                description=p.description or "",
                resource=p.resource,
                action=p.action,
            )
            for p in role.permissions
        ],
        created_at=role.created_at,
        updated_at=role.updated_at,
    )

    return APIResponse.ok(data=response, message="Permission removed from role")


@router.get(
    "/permissions/all",
    response_model=APIResponse[List[PermissionResponse]],
    summary="List all permissions",
    description="Retrieve all available permissions in the system.",
    dependencies=[Depends(require_permissions(["roles:read"]))],
)
async def list_permissions(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[List[PermissionResponse]]:
    """List all available permissions."""
    stmt = select(Permission).order_by(Permission.name)
    result = await session.execute(stmt)
    permissions = result.scalars().all()

    responses = [
        PermissionResponse(
            id=p.id,
            name=p.name,
            description=p.description or "",
            resource=p.resource,
            action=p.action,
        )
        for p in permissions
    ]

    return APIResponse.ok(data=responses, message="Permissions retrieved successfully")
