"""
ExamShield - Center Release Key Repository
"""
import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.center_release_key import CenterReleaseKey
from app.repositories.base_repository import BaseRepository

class CenterReleaseKeyRepository(BaseRepository[CenterReleaseKey]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(CenterReleaseKey, session)

    async def get_by_center_and_paper(
        self, center_id: uuid.UUID, paper_id: uuid.UUID
    ) -> Optional[CenterReleaseKey]:
        stmt = select(CenterReleaseKey).where(
            CenterReleaseKey.examination_center_id == center_id,
            CenterReleaseKey.question_paper_id == paper_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
