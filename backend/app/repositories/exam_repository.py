"""
ExamShield - Exam Repository

Data access layer for exam CRUD operations.
Extends BaseRepository with exam-specific query methods.
"""

import uuid
from typing import Dict, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.exam import Exam
from app.repositories.base_repository import BaseRepository


class ExamRepository(BaseRepository[Exam]):
    """
    Repository for Exam entity database operations.

    Provides exam-specific queries on top of the generic
    BaseRepository CRUD methods.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Exam, session)

    async def get_by_exam_code(self, exam_code: str) -> Optional[Exam]:
        """
        Retrieve an exam by its unique code.

        Args:
            exam_code: The unique examination code.

        Returns:
            The Exam if found, None otherwise.
        """
        stmt = select(Exam).where(Exam.exam_code == exam_code)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def exam_code_exists(self, exam_code: str) -> bool:
        """
        Check whether an exam with the given code already exists.

        Args:
            exam_code: The exam code to check.

        Returns:
            True if the code is taken, False otherwise.
        """
        stmt = (
            select(func.count())
            .select_from(Exam)
            .where(Exam.exam_code == exam_code)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def get_with_creator(self, exam_id: uuid.UUID) -> Optional[Exam]:
        """
        Retrieve an exam with its creator relationship eagerly loaded.

        Args:
            exam_id: The UUID of the exam.

        Returns:
            The Exam with creator loaded, or None.
        """
        stmt = (
            select(Exam)
            .options(selectinload(Exam.creator))
            .where(Exam.id == exam_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_exams(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[Exam]:
        """
        Retrieve a filtered, paginated list of exams.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            search: Optional search term for exam_code or exam_name.
            year: Optional year filter.

        Returns:
            List of Exam entities.
        """
        stmt = (
            select(Exam)
            .options(selectinload(Exam.creator))
            .order_by(Exam.created_at.desc())
        )

        if status:
            stmt = stmt.where(Exam.status == status)
        if year:
            stmt = stmt.where(Exam.year == year)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                Exam.exam_code.ilike(search_term)
                | Exam.exam_name.ilike(search_term)
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
    ) -> int:
        """
        Count exams matching the given filters.

        Args:
            status: Optional status filter.
            search: Optional search term for exam_code or exam_name.
            year: Optional year filter.

        Returns:
            Count of matching exams.
        """
        stmt = select(func.count()).select_from(Exam)

        if status:
            stmt = stmt.where(Exam.status == status)
        if year:
            stmt = stmt.where(Exam.year == year)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                Exam.exam_code.ilike(search_term)
                | Exam.exam_name.ilike(search_term)
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_status(self) -> Dict[str, int]:
        """
        Count exams grouped by status.

        Returns:
            Dictionary mapping status names to counts.
        """
        stmt = (
            select(Exam.status, func.count(Exam.id))
            .group_by(Exam.status)
        )
        result = await self._session.execute(stmt)
        return dict(result.all())
