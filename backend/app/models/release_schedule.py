"""
ExamShield - Release Schedule Model

Defines the ReleaseSchedule ORM model representing the configured
release time and status for a question paper.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ReleaseStatus:
    """Allowed status values for a release schedule."""

    SCHEDULED = "scheduled"
    RELEASED = "released"
    FAILED = "failed"


class ReleaseSchedule(UUIDMixin, TimestampMixin, Base):
    """
    Release Schedule model configuring when a paper should be securely distributed.
    """

    __tablename__ = "release_schedules"

    question_paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    release_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ReleaseStatus.SCHEDULED,
        index=True,
    )
    
    scheduled_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Relationships ────────────────────────────────────────────
    question_paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper",
        lazy="selectin",
    )
    scheduler: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[scheduled_by],
    )

    def __repr__(self) -> str:
        return (
            f"<ReleaseSchedule(id={self.id}, paper_id={self.question_paper_id}, "
            f"release_at='{self.release_at}', status='{self.status}')>"
        )
