"""
ExamShield - Subject Repository

Data access layer for subject CRUD operations.
Extends BaseRepository with subject-specific query methods.
"""

import uuid
from typing import Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class SubjectRepository(BaseRepository[Subject]):
    """
    Repository for Subject entity database operations.

    Provides subject-specific queries on top of the generic
    BaseRepository CRUD methods.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(Subject, session)

    async def get_by_subject_code(
        self,
        exam_id: uuid.UUID,
        subject_code: str,
    ) -> Optional[Subject]:
        """
        Retrieve a subject by its code within a specific exam.

        Args:
            exam_id: The UUID of the parent exam.
            subject_code: The subject code to look up.

        Returns:
            The Subject if found, None otherwise.
        """
        stmt = select(Subject).where(
            and_(
                Subject.exam_id == exam_id,
                Subject.subject_code == subject_code,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def subject_code_exists(
        self,
        exam_id: uuid.UUID,
        subject_code: str,
    ) -> bool:
        """
        Check whether a subject with the given code already exists in the exam.

        Args:
            exam_id: The UUID of the parent exam.
            subject_code: The subject code to check.

        Returns:
            True if the code is taken within the exam, False otherwise.
        """
        stmt = (
            select(func.count())
            .select_from(Subject)
            .where(
                and_(
                    Subject.exam_id == exam_id,
                    Subject.subject_code == subject_code,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def get_with_relations(
        self,
        subject_id: uuid.UUID,
    ) -> Optional[Subject]:
        """
        Retrieve a subject with its exam and creator relationships eagerly loaded.

        Args:
            subject_id: The UUID of the subject.

        Returns:
            The Subject with relationships loaded, or None.
        """
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.exam),
                selectinload(Subject.creator),
            )
            .where(Subject.id == subject_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_subjects(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        exam_id: Optional[uuid.UUID] = None,
    ) -> List[Subject]:
        """
        Retrieve a filtered, paginated list of subjects.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            search: Optional search term for subject_code or subject_name.
            exam_id: Optional exam filter.

        Returns:
            List of Subject entities.
        """
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.exam),
                selectinload(Subject.creator),
            )
            .order_by(Subject.created_at.desc())
        )

        if status:
            stmt = stmt.where(Subject.status == status)
        if exam_id:
            stmt = stmt.where(Subject.exam_id == exam_id)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                Subject.subject_code.ilike(search_term)
                | Subject.subject_name.ilike(search_term)
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_exam(
        self,
        exam_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Subject]:
        """
        Retrieve all subjects belonging to a specific exam.

        Args:
            exam_id: The UUID of the parent exam.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of Subject entities for the exam.
        """
        stmt = (
            select(Subject)
            .options(
                selectinload(Subject.exam),
                selectinload(Subject.creator),
            )
            .where(Subject.exam_id == exam_id)
            .order_by(Subject.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        exam_id: Optional[uuid.UUID] = None,
    ) -> int:
        """
        Count subjects matching the given filters.

        Args:
            status: Optional status filter.
            search: Optional search term for subject_code or subject_name.
            exam_id: Optional exam filter.

        Returns:
            Count of matching subjects.
        """
        stmt = select(func.count()).select_from(Subject)

        if status:
            stmt = stmt.where(Subject.status == status)
        if exam_id:
            stmt = stmt.where(Subject.exam_id == exam_id)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                Subject.subject_code.ilike(search_term)
                | Subject.subject_name.ilike(search_term)
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_status(self) -> Dict[str, int]:
        """
        Count subjects grouped by status.

        Returns:
            Dictionary mapping status names to counts.
        """
        stmt = (
            select(Subject.status, func.count(Subject.id))
            .group_by(Subject.status)
        )
        result = await self._session.execute(stmt)
        return dict(result.all())

    async def count_by_exam(self, exam_id: uuid.UUID) -> int:
        """
        Count subjects belonging to a specific exam.

        Args:
            exam_id: The UUID of the parent exam.

        Returns:
            Count of subjects for the exam.
        """
        stmt = (
            select(func.count())
            .select_from(Subject)
            .where(Subject.exam_id == exam_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()
