"""
ExamShield - Subject Model

Defines the Subject ORM model representing a subject within an examination.
Each subject belongs to exactly one exam and has a unique code per exam scope.
"""

import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class SubjectStatus:
    """Allowed status values for a subject."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"

    ALL = {DRAFT, ACTIVE, ARCHIVED}

    TRANSITIONS = {
        DRAFT: {ACTIVE},
        ACTIVE: {ARCHIVED},
        ARCHIVED: set(),
    }

    @classmethod
    def is_valid_transition(cls, current: str, target: str) -> bool:
        """Check whether a status transition is allowed."""
        allowed = cls.TRANSITIONS.get(current, set())
        return target in allowed


class Subject(UUIDMixin, TimestampMixin, Base):
    """
    Subject model for managing subjects within an examination.

    Each subject has a unique code within its parent exam and follows
    a strict status progression: Draft → Active → Archived.
    """

    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint(
            "exam_id",
            "subject_code",
            name="uq_subject_code_per_exam",
        ),
    )

    exam_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    subject_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    language: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=SubjectStatus.DRAFT,
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
    exam: Mapped["Exam"] = relationship(
        "Exam",
        back_populates="subjects",
        lazy="selectin",
    )
    creator: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[created_by],
    )
    question_papers: Mapped[List["QuestionPaper"]] = relationship(
        "QuestionPaper",
        back_populates="subject",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Subject(id={self.id}, code='{self.subject_code}', "
            f"exam_id={self.exam_id}, status='{self.status}')>"
        )

    @property
    def exam_name(self) -> Optional[str]:
        """Return the name of the parent exam, or None if unresolvable."""
        return self.exam.exam_name if self.exam else None

    @property
    def creator_name(self) -> Optional[str]:
        """Return the name of the subject creator, or None if unresolvable."""
        return self.creator.full_name if self.creator else None
