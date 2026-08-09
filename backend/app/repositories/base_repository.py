"""
ExamShield - Base Repository

Generic repository providing async CRUD operations for any SQLAlchemy model.
All concrete repositories inherit from this class.
"""

import uuid
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Generic async repository implementing common CRUD operations.

    Type Parameters:
        ModelType: The SQLAlchemy model class this repository manages.
    """

    def __init__(self, model: Type[ModelType], session: AsyncSession) -> None:
        self._model = model
        self._session = session

    async def get_by_id(self, entity_id: uuid.UUID) -> Optional[ModelType]:
        """
        Retrieve a single entity by its UUID primary key.

        Args:
            entity_id: The UUID of the entity to retrieve.

        Returns:
            The entity if found, None otherwise.
        """
        stmt = select(self._model).where(self._model.id == entity_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Retrieve a paginated list of all entities.

        Args:
            skip: Number of records to skip (offset).
            limit: Maximum number of records to return.

        Returns:
            List of entities.
        """
        stmt = select(self._model).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_field(
        self,
        field_name: str,
        value: Any,
    ) -> Optional[ModelType]:
        """
        Retrieve a single entity by a specific field value.

        Args:
            field_name: The name of the model field to filter on.
            value: The value to match.

        Returns:
            The entity if found, None otherwise.
        """
        column = getattr(self._model, field_name)
        stmt = select(self._model).where(column == value)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_many_by_field(
        self,
        field_name: str,
        value: Any,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """
        Retrieve multiple entities matching a specific field value.

        Args:
            field_name: The name of the model field to filter on.
            value: The value to match.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of matching entities.
        """
        column = getattr(self._model, field_name)
        stmt = (
            select(self._model)
            .where(column == value)
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, entity_data: Dict[str, Any]) -> ModelType:
        """
        Create a new entity from a dictionary of field values.

        Args:
            entity_data: Dictionary mapping field names to values.

        Returns:
            The newly created entity.
        """
        entity = self._model(**entity_data)
        self._session.add(entity)
        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def update(
        self,
        entity_id: uuid.UUID,
        update_data: Dict[str, Any],
    ) -> Optional[ModelType]:
        """
        Update an existing entity by its UUID.

        Args:
            entity_id: The UUID of the entity to update.
            update_data: Dictionary of fields to update.

        Returns:
            The updated entity if found, None otherwise.
        """
        entity = await self.get_by_id(entity_id)
        if entity is None:
            return None

        for field, value in update_data.items():
            setattr(entity, field, value)

        await self._session.flush()
        await self._session.refresh(entity)
        return entity

    async def delete(self, entity_id: uuid.UUID) -> bool:
        """
        Delete an entity by its UUID.

        Args:
            entity_id: The UUID of the entity to delete.

        Returns:
            True if the entity was deleted, False if not found.
        """
        stmt = (
            delete(self._model)
            .where(self._model.id == entity_id)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.rowcount > 0

    async def count(self) -> int:
        """
        Count the total number of entities.

        Returns:
            Total count of entities in the table.
        """
        stmt = select(func.count()).select_from(self._model)
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def exists(self, entity_id: uuid.UUID) -> bool:
        """
        Check whether an entity with the given UUID exists.

        Args:
            entity_id: The UUID to check.

        Returns:
            True if the entity exists, False otherwise.
        """
        stmt = (
            select(func.count())
            .select_from(self._model)
            .where(self._model.id == entity_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0
