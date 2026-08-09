"""
ExamShield - Approval Workflow Repository

Data access layer for approval workflow stages.
"""

import uuid
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.approval_workflow import ApprovalDecision, ApprovalWorkflow
from app.models.question_paper import QuestionPaper
from app.repositories.base_repository import BaseRepository


class ApprovalWorkflowRepository(BaseRepository[ApprovalWorkflow]):
    """
    Repository for ApprovalWorkflow entity database operations.
    """

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(ApprovalWorkflow, session)

    async def get_workflow_history(self, paper_id: uuid.UUID) -> List[ApprovalWorkflow]:
        """
        Get the full chronological approval history for a question paper.
        """
        stmt = (
            select(ApprovalWorkflow)
            .options(selectinload(ApprovalWorkflow.approver))
            .where(ApprovalWorkflow.question_paper_id == paper_id)
            .order_by(ApprovalWorkflow.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_pending_stage(self, paper_id: uuid.UUID) -> Optional[ApprovalWorkflow]:
        """
        Get the currently pending approval stage for a question paper.
        """
        stmt = (
            select(ApprovalWorkflow)
            .where(
                and_(
                    ApprovalWorkflow.question_paper_id == paper_id,
                    ApprovalWorkflow.decision == ApprovalDecision.PENDING,
                )
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_pending_approvals(self, level: str) -> List[QuestionPaper]:
        """
        Get all question papers currently pending approval at the specified level.
        """
        stmt = (
            select(QuestionPaper)
            .join(ApprovalWorkflow)
            .options(
                selectinload(QuestionPaper.subject),
                selectinload(QuestionPaper.uploader),
            )
            .where(
                and_(
                    ApprovalWorkflow.decision == ApprovalDecision.PENDING,
                    ApprovalWorkflow.approval_level == level,
                )
            )
            .order_by(QuestionPaper.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
