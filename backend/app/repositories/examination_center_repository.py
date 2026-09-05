"""
ExamShield - Examination Center Repository

Data access layer for the ExaminationCenter model.
"""

import uuid
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.examination_center import ExaminationCenter, CenterStatus
from app.repositories.base_repository import BaseRepository


class ExaminationCenterRepository(BaseRepository[ExaminationCenter]):
    """
    Repository for managing examination centers in the database.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ExaminationCenter, session)

    async def get_by_code(self, center_code: str) -> Optional[ExaminationCenter]:
        """Fetch a center by its unique code."""
        stmt = select(ExaminationCenter).where(ExaminationCenter.center_code == center_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_centers(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ExaminationCenter]:
        """List and optionally filter centers."""
        stmt = select(ExaminationCenter).offset(skip).limit(limit)

        if status:
            stmt = stmt.where(ExaminationCenter.status == status)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                ExaminationCenter.center_code.ilike(search_pattern)
                | ExaminationCenter.name.ilike(search_pattern)
            )

        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_exams(self, center_id: uuid.UUID) -> Optional[ExaminationCenter]:
        """Fetch a center along with its associated exams."""
        stmt = (
            select(ExaminationCenter)
            .where(ExaminationCenter.id == center_id)
            .options(selectinload(ExaminationCenter.exams))
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
