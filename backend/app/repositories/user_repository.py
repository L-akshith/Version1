"""
ExamShield - User Repository

Provides data access operations specific to the User model,
extending the generic BaseRepository.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User
from app.models.role import Role
from app.repositories.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User model operations.

    Extends BaseRepository with user-specific queries such as
    lookup by email and eager loading of role relationships.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user by their email address.

        Args:
            email: The email address to look up.

        Returns:
            The User if found, None otherwise.
        """
        stmt = (
            select(User)
            .where(User.email == email)
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_role(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user with their role and permissions eagerly loaded.

        Args:
            user_id: The UUID of the user.

        Returns:
            The User with role data if found, None otherwise.
        """
        stmt = (
            select(User)
            .where(User.id == user_id)
            .options(selectinload(User.role).selectinload(Role.permissions))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_with_roles(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Retrieve all users with their roles eagerly loaded.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Users with role data.
        """
        stmt = (
            select(User)
            .options(selectinload(User.role).selectinload(Role.permissions))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[User]:
        """
        Retrieve all active users.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of active Users.
        """
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .options(selectinload(User.role))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.

        Args:
            email: The email address to check.

        Returns:
            True if the email is taken, False otherwise.
        """
        user = await self.get_by_email(email)
        return user is not None

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> Optional[User]:
        """
        Assign a role to a user.

        Args:
            user_id: The UUID of the user.
            role_id: The UUID of the role to assign.

        Returns:
            The updated User if found, None otherwise.
        """
        return await self.update(user_id, {"role_id": role_id})

    async def deactivate(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Deactivate a user account.

        Args:
            user_id: The UUID of the user to deactivate.

        Returns:
            The updated User if found, None otherwise.
        """
        return await self.update(user_id, {"is_active": False})

    async def activate(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Activate a user account.

        Args:
            user_id: The UUID of the user to activate.

        Returns:
            The updated User if found, None otherwise.
        """
        return await self.update(user_id, {"is_active": True})
