"""
ExamShield - Release Schedule Repository
"""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.release_schedule import ReleaseSchedule, ReleaseStatus
from app.repositories.base_repository import BaseRepository

class ReleaseScheduleRepository(BaseRepository[ReleaseSchedule]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ReleaseSchedule, session)

    async def get_by_paper_id(
        self,
        paper_id: uuid.UUID,
        *,
        for_update: bool = False,
    ) -> Optional[ReleaseSchedule]:
        stmt = select(ReleaseSchedule).where(
            ReleaseSchedule.question_paper_id == paper_id
        )
        if for_update:
            stmt = stmt.with_for_update()
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_schedules(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[ReleaseSchedule]:
        stmt = select(ReleaseSchedule)
        if status:
            stmt = stmt.where(ReleaseSchedule.status == status)
        stmt = stmt.order_by(ReleaseSchedule.created_at.desc()).offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

