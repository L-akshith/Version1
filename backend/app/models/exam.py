"""
ExamShield - Exam Model

Defines the Exam ORM model representing an examination entry
with lifecycle status tracking and conducting authority metadata.
"""

import uuid
from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class ExamStatus:
    """Allowed status values for an examination."""

    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"

    ALL = {DRAFT, SCHEDULED, ACTIVE, COMPLETED, ARCHIVED}

    TRANSITIONS = {
        DRAFT: {SCHEDULED},
        SCHEDULED: {ACTIVE},
        ACTIVE: {COMPLETED},
        COMPLETED: {ARCHIVED},
        ARCHIVED: set(),
    }

    @classmethod
    def is_valid_transition(cls, current: str, target: str) -> bool:
        """Check whether a status transition is allowed."""
        allowed = cls.TRANSITIONS.get(current, set())
        return target in allowed


class Exam(UUIDMixin, TimestampMixin, Base):
    """
    Exam model for examination lifecycle management.

    Each exam has a unique code, belongs to a conducting authority,
    and follows a strict status progression:
    Draft → Scheduled → Active → Completed → Archived.
    """

    __tablename__ = "exams"

    exam_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    exam_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    conducting_authority: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    year: Mapped[int] = mapped_column(
        nullable=False,
    )
    exam_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=ExamStatus.DRAFT,
        index=True,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    creator: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[created_by],
    )

    def __repr__(self) -> str:
        return f"<Exam(id={self.id}, code='{self.exam_code}', status='{self.status}')>"

    @property
    def creator_name(self) -> Optional[str]:
        """Return the name of the exam creator, or None if unresolvable."""
        return self.creator.full_name if self.creator else None
