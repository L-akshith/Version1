"""
ExamShield - Role Repository

Provides data access operations specific to the Role model,
extending the generic BaseRepository.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.role import Role
from app.models.permission import Permission
from app.repositories.base_repository import BaseRepository


class RoleRepository(BaseRepository[Role]):
    """
    Repository for Role model operations.

    Extends BaseRepository with role-specific queries such as
    lookup by name and permission management.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Role, session)

    async def get_by_name(self, name: str) -> Optional[Role]:
        """
        Retrieve a role by its name.

        Args:
            name: The role name to look up.

        Returns:
            The Role if found, None otherwise.
        """
        stmt = (
            select(Role)
            .where(Role.name == name)
            .options(selectinload(Role.permissions))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_permissions(self, role_id: uuid.UUID) -> Optional[Role]:
        """
        Retrieve a role with its permissions eagerly loaded.

        Args:
            role_id: The UUID of the role.

        Returns:
            The Role with permissions if found, None otherwise.
        """
        stmt = (
            select(Role)
            .where(Role.id == role_id)
            .options(selectinload(Role.permissions))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_permissions(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Role]:
        """
        Retrieve all roles with their permissions eagerly loaded.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Roles with permission data.
        """
        stmt = (
            select(Role)
            .options(selectinload(Role.permissions))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def name_exists(self, name: str) -> bool:
        """
        Check if a role name is already taken.

        Args:
            name: The role name to check.

        Returns:
            True if the name is taken, False otherwise.
        """
        role = await self.get_by_name(name)
        return role is not None

    async def add_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Optional[Role]:
        """
        Add a permission to a role.

        Args:
            role_id: The UUID of the role.
            permission_id: The UUID of the permission to add.

        Returns:
            The updated Role if found, None otherwise.
        """
        role = await self.get_with_permissions(role_id)
        if role is None:
            return None

        perm_stmt = select(Permission).where(Permission.id == permission_id)
        perm_result = await self._session.execute(perm_stmt)
        permission = perm_result.scalar_one_or_none()

        if permission is None:
            return None

        if permission not in role.permissions:
            role.permissions.append(permission)
            await self._session.flush()
            await self._session.refresh(role)

        return role

    async def remove_permission(
        self,
        role_id: uuid.UUID,
        permission_id: uuid.UUID,
    ) -> Optional[Role]:
        """
        Remove a permission from a role.

        Args:
            role_id: The UUID of the role.
            permission_id: The UUID of the permission to remove.

        Returns:
            The updated Role if found, None otherwise.
        """
        role = await self.get_with_permissions(role_id)
        if role is None:
            return None

        role.permissions = [
            p for p in role.permissions if p.id != permission_id
        ]
        await self._session.flush()
        await self._session.refresh(role)

        return role
