"""
ExamShield - Question Paper Repository

Data access layer for question paper CRUD operations.
Extends BaseRepository with paper-specific query methods
including version management, filtering, and statistics.
"""

import uuid
from typing import Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.repositories.base_repository import BaseRepository


class QuestionPaperRepository(BaseRepository[QuestionPaper]):
    """
    Repository for QuestionPaper entity database operations.

    Provides paper-specific queries including version management,
    filtered listing, and statistics aggregation.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(QuestionPaper, session)

    async def get_with_relations(
        self,
        paper_id: uuid.UUID,
    ) -> Optional[QuestionPaper]:
        """
        Retrieve a question paper with all relationships eagerly loaded.

        Args:
            paper_id: The UUID of the paper.

        Returns:
            The QuestionPaper with relationships loaded, or None.
        """
        stmt = (
            select(QuestionPaper)
            .options(
                selectinload(QuestionPaper.subject).selectinload(Subject.exam),
                selectinload(QuestionPaper.uploader),
                selectinload(QuestionPaper.approver),
            )
            .where(QuestionPaper.id == paper_id)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_papers(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        subject_id: Optional[uuid.UUID] = None,
    ) -> List[QuestionPaper]:
        """
        Retrieve a filtered, paginated list of question papers.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            search: Optional search term for paper_code or title.
            subject_id: Optional subject filter.

        Returns:
            List of QuestionPaper entities.
        """
        stmt = (
            select(QuestionPaper)
            .options(
                selectinload(QuestionPaper.subject).selectinload(Subject.exam),
                selectinload(QuestionPaper.uploader),
                selectinload(QuestionPaper.approver),
            )
            .order_by(QuestionPaper.created_at.desc())
        )

        if status:
            stmt = stmt.where(QuestionPaper.status == status)
        if subject_id:
            stmt = stmt.where(QuestionPaper.subject_id == subject_id)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                QuestionPaper.paper_code.ilike(search_term)
                | QuestionPaper.title.ilike(search_term)
            )

        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_by_subject(
        self,
        subject_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[QuestionPaper]:
        """
        Retrieve all question papers belonging to a specific subject.

        Args:
            subject_id: The UUID of the parent subject.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of QuestionPaper entities.
        """
        stmt = (
            select(QuestionPaper)
            .options(
                selectinload(QuestionPaper.subject).selectinload(Subject.exam),
                selectinload(QuestionPaper.uploader),
                selectinload(QuestionPaper.approver),
            )
            .where(QuestionPaper.subject_id == subject_id)
            .order_by(QuestionPaper.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_versions(
        self,
        subject_id: uuid.UUID,
        paper_code: str,
    ) -> List[QuestionPaper]:
        """
        Retrieve all versions of a paper by subject and code.

        Args:
            subject_id: The UUID of the parent subject.
            paper_code: The paper code to look up.

        Returns:
            List of QuestionPaper entities ordered by version descending.
        """
        stmt = (
            select(QuestionPaper)
            .options(
                selectinload(QuestionPaper.uploader),
            )
            .where(
                and_(
                    QuestionPaper.subject_id == subject_id,
                    QuestionPaper.paper_code == paper_code,
                )
            )
            .order_by(desc(QuestionPaper.version))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def latest_version(
        self,
        subject_id: uuid.UUID,
        paper_code: str,
    ) -> int:
        """
        Get the highest version number for a paper code within a subject.

        Args:
            subject_id: The UUID of the parent subject.
            paper_code: The paper code to check.

        Returns:
            The highest version number, or 0 if no versions exist.
        """
        stmt = (
            select(func.coalesce(func.max(QuestionPaper.version), 0))
            .where(
                and_(
                    QuestionPaper.subject_id == subject_id,
                    QuestionPaper.paper_code == paper_code,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def paper_code_version_exists(
        self,
        subject_id: uuid.UUID,
        paper_code: str,
        version: int,
    ) -> bool:
        """
        Check if a specific paper code + version combination exists.

        Args:
            subject_id: The UUID of the parent subject.
            paper_code: The paper code.
            version: The version number.

        Returns:
            True if the combination exists, False otherwise.
        """
        stmt = (
            select(func.count())
            .select_from(QuestionPaper)
            .where(
                and_(
                    QuestionPaper.subject_id == subject_id,
                    QuestionPaper.paper_code == paper_code,
                    QuestionPaper.version == version,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one() > 0

    async def count_filtered(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        subject_id: Optional[uuid.UUID] = None,
    ) -> int:
        """
        Count question papers matching the given filters.

        Args:
            status: Optional status filter.
            search: Optional search term.
            subject_id: Optional subject filter.

        Returns:
            Count of matching papers.
        """
        stmt = select(func.count()).select_from(QuestionPaper)

        if status:
            stmt = stmt.where(QuestionPaper.status == status)
        if subject_id:
            stmt = stmt.where(QuestionPaper.subject_id == subject_id)
        if search:
            search_term = f"%{search}%"
            stmt = stmt.where(
                QuestionPaper.paper_code.ilike(search_term)
                | QuestionPaper.title.ilike(search_term)
            )

        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_by_status(self) -> Dict[str, int]:
        """
        Count question papers grouped by status.

        Returns:
            Dictionary mapping status names to counts.
        """
        stmt = (
            select(QuestionPaper.status, func.count(QuestionPaper.id))
            .group_by(QuestionPaper.status)
        )
        result = await self._session.execute(stmt)
        return dict(result.all())
