"""
ExamShield - Approval Workflow Model

Defines the ApprovalWorkflow ORM model representing the multi-level
approval process for question papers. It records each decision stage,
approver, and timestamp.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.question_paper import QuestionPaper
    from app.models.user import User


class ApprovalLevel:
    """Approval hierarchy levels in order of execution."""

    QUESTION_SETTER = "Question Setter"
    MODERATOR = "Moderator"
    CHIEF_CONTROLLER = "Controller"
    EXAM_AUTHORITY = "Admin"

    ORDER = [
        QUESTION_SETTER,
        MODERATOR,
        CHIEF_CONTROLLER,
        EXAM_AUTHORITY,
    ]


class ApprovalDecision:
    """Allowed decisions for a workflow stage."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    RETURNED = "returned"  # Returned for revision


class ApprovalWorkflow(UUIDMixin, TimestampMixin, Base):
    """
    Approval Workflow model tracking the lifecycle of a question paper
    through multiple authorization stages.
    """

    __tablename__ = "approval_workflows"
    __table_args__ = (
        UniqueConstraint(
            "question_paper_id",
            "approval_level",
            "decision",
            name="uq_pending_approval_level_per_paper",
        ),
    )

    question_paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    approval_level: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    approver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Null when pending
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ApprovalDecision.PENDING,
        index=True,
    )
    remarks: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    question_paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper",
        back_populates="workflows",
        lazy="selectin",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<ApprovalWorkflow(id={self.id}, level='{self.approval_level}', "
            f"decision='{self.decision}')>"
        )

    @property
    def approver_name(self) -> Optional[str]:
        """Return the full name of the approver."""
        return self.approver.full_name if self.approver else None
