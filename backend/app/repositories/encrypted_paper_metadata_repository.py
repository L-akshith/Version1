"""
ExamShield - Encrypted Paper Metadata Repository

Data access layer for EncryptedPaperMetadata operations.
"""

import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.repositories.base_repository import BaseRepository


class EncryptedPaperMetadataRepository(BaseRepository[EncryptedPaperMetadata]):
    """
    Repository for EncryptedPaperMetadata database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(EncryptedPaperMetadata, session)

    async def get_by_question_paper_id(self, question_paper_id: uuid.UUID) -> Optional[EncryptedPaperMetadata]:
        """
        Retrieve metadata associated with a specific question paper.

        Args:
            question_paper_id: The UUID of the question paper.

        Returns:
            The EncryptedPaperMetadata if found, None otherwise.
        """
        stmt = select(EncryptedPaperMetadata).where(
            EncryptedPaperMetadata.question_paper_id == question_paper_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_with_paper(self, metadata_id: uuid.UUID) -> Optional[EncryptedPaperMetadata]:
        """
        Retrieve metadata with its parent question paper eagerly loaded.

        Args:
            metadata_id: The UUID of the metadata record.

        Returns:
            The EncryptedPaperMetadata if found, None otherwise.
        """
        stmt = (
            select(EncryptedPaperMetadata)
            .options(selectinload(EncryptedPaperMetadata.question_paper))
            .where(EncryptedPaperMetadata.id == metadata_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
