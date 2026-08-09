"""
ExamShield - Key Metadata Repository
"""

import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.key_metadata import KeyMetadata
from app.repositories.base_repository import BaseRepository


class KeyMetadataRepository(BaseRepository[KeyMetadata]):
    """
    Data access layer for KeyMetadata.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(KeyMetadata, session)

    async def get_by_identifier(self, key_identifier: str) -> KeyMetadata | None:
        stmt = select(KeyMetadata).where(KeyMetadata.key_identifier == key_identifier)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_keys(self) -> List[KeyMetadata]:
        stmt = select(KeyMetadata).order_by(KeyMetadata.created_at.desc())
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
