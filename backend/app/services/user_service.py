"""
ExamShield - User Service

Business logic for user management operations including
CRUD, role assignment, and user lifecycle management.
"""

import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import ConflictException, NotFoundException
from app.exceptions.authorization import RoleNotFoundException
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserResponse, UserUpdate
from app.utils.password import hash_password


class UserService:
    """
    Service layer for user management operations.

    Implements user CRUD, role assignment, and lifecycle management
    following the Clean Architecture pattern.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._role_repo = RoleRepository(session)

    async def get_user(self, user_id: uuid.UUID) -> UserResponse:
        """
        Retrieve a single user by ID.

        Args:
            user_id: The UUID of the user to retrieve.

        Returns:
            UserResponse with the user's data.

        Raises:
            NotFoundException: If the user does not exist.
        """
        user = await self._user_repo.get_with_role(user_id)
        if user is None:
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        return UserResponse.model_validate({
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "role_id": user.role_id,
            "role_name": user.role_name,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        })

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[UserResponse]:
        """
        Retrieve a paginated list of all users.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of UserResponse objects.
        """
        users = await self._user_repo.get_all_with_roles(skip=skip, limit=limit)
        return [
            UserResponse.model_validate({
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_superuser": user.is_superuser,
                "role_id": user.role_id,
                "role_name": user.role_name,
                "created_at": user.created_at,
                "updated_at": user.updated_at,
            })
            for user in users
        ]

    async def update_user(
        self,
        user_id: uuid.UUID,
        update_data: UserUpdate,
    ) -> UserResponse:
        """
        Update a user's profile information.

        Args:
            user_id: The UUID of the user to update.
            update_data: The fields to update.

        Returns:
            UserResponse with the updated user's data.

        Raises:
            NotFoundException: If the user does not exist.
            ConflictException: If the new email is already taken.
        """
        existing = await self._user_repo.get_by_id(user_id)
        if existing is None:
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        data: Dict[str, Any] = update_data.model_dump(exclude_unset=True)

        if "email" in data and data["email"] != existing.email:
            if await self._user_repo.email_exists(data["email"]):
                raise ConflictException(
                    message=f"Email '{data['email']}' is already registered"
                )

        if "password" in data:
            data["hashed_password"] = hash_password(data.pop("password"))

        if not data:
            return await self.get_user(user_id)

        await self._user_repo.update(user_id, data)
        return await self.get_user(user_id)

    async def delete_user(self, user_id: uuid.UUID) -> bool:
        """
        Delete a user by ID.

        Args:
            user_id: The UUID of the user to delete.

        Returns:
            True if the user was deleted.

        Raises:
            NotFoundException: If the user does not exist.
        """
        if not await self._user_repo.exists(user_id):
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        return await self._user_repo.delete(user_id)

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
    ) -> UserResponse:
        """
        Assign a role to a user.

        Args:
            user_id: The UUID of the user.
            role_id: The UUID of the role to assign.

        Returns:
            UserResponse with the updated user's data.

        Raises:
            NotFoundException: If the user does not exist.
            RoleNotFoundException: If the role does not exist.
        """
        if not await self._user_repo.exists(user_id):
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        if not await self._role_repo.exists(role_id):
            raise RoleNotFoundException(
                message=f"Role with ID '{role_id}' not found"
            )

        await self._user_repo.assign_role(user_id, role_id)
        return await self.get_user(user_id)

    async def deactivate_user(self, user_id: uuid.UUID) -> UserResponse:
        """
        Deactivate a user account.

        Args:
            user_id: The UUID of the user to deactivate.

        Returns:
            UserResponse with the updated user's data.

        Raises:
            NotFoundException: If the user does not exist.
        """
        if not await self._user_repo.exists(user_id):
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        await self._user_repo.deactivate(user_id)
        return await self.get_user(user_id)

    async def activate_user(self, user_id: uuid.UUID) -> UserResponse:
        """
        Activate a user account.

        Args:
            user_id: The UUID of the user to activate.

        Returns:
            UserResponse with the updated user's data.

        Raises:
            NotFoundException: If the user does not exist.
        """
        if not await self._user_repo.exists(user_id):
            raise NotFoundException(message=f"User with ID '{user_id}' not found")

        await self._user_repo.activate(user_id)
        return await self.get_user(user_id)

    async def get_user_count(self) -> int:
        """Return the total number of users."""
        return await self._user_repo.count()
