"""
ExamShield - Question Paper Model

Defines the QuestionPaper ORM model representing an uploaded examination
question paper. Each paper belongs to exactly one Subject and supports
full version control with SHA-256 integrity hashing.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class QuestionPaperStatus:
    """Allowed status values for a question paper."""

    DRAFT = "draft"
    UPLOADED = "uploaded"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

    ALL = {DRAFT, UPLOADED, UNDER_REVIEW, APPROVED, REJECTED, ARCHIVED}

    TRANSITIONS = {
        DRAFT: {UPLOADED},
        UPLOADED: {UNDER_REVIEW},
        UNDER_REVIEW: {APPROVED, REJECTED},
        APPROVED: {ARCHIVED},
        REJECTED: {DRAFT},
        ARCHIVED: set(),
    }

    @classmethod
    def is_valid_transition(cls, current: str, target: str) -> bool:
        """Check whether a status transition is allowed."""
        allowed = cls.TRANSITIONS.get(current, set())
        return target in allowed


class QuestionPaper(UUIDMixin, TimestampMixin, Base):
    """
    Question Paper model for examination paper lifecycle management.

    Each paper belongs to a Subject, has version control, and stores
    a SHA-256 hash for integrity verification. Papers follow a strict
    status progression through their lifecycle.
    """

    __tablename__ = "question_papers"
    __table_args__ = (
        UniqueConstraint(
            "subject_id",
            "paper_code",
            "version",
            name="uq_paper_code_version_per_subject",
        ),
    )

    # ── Core Fields ──────────────────────────────────────────────
    subject_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    paper_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=QuestionPaperStatus.DRAFT,
        index=True,
    )

    # ── File Metadata ────────────────────────────────────────────
    file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    original_file_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    sha256_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=False,
        index=True,
    )
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    upload_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ────────────────────────────────────────────
    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="question_papers",
        lazy="selectin",
    )
    uploader: Mapped["User"] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[uploaded_by],
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        lazy="selectin",
        foreign_keys=[approved_by],
    )
    workflows: Mapped[List["ApprovalWorkflow"]] = relationship(
        "ApprovalWorkflow",
        back_populates="question_paper",
        lazy="selectin",
        cascade="all, delete-orphan",
        order_by="desc(ApprovalWorkflow.created_at)",
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionPaper(id={self.id}, code='{self.paper_code}', "
            f"v{self.version}, status='{self.status}')>"
        )

    @property
    def subject_name(self) -> Optional[str]:
        """Return the name of the parent subject."""
        return self.subject.subject_name if self.subject else None

    @property
    def exam_name(self) -> Optional[str]:
        """Return the name of the parent exam via the subject."""
        if self.subject and self.subject.exam:
            return self.subject.exam.exam_name
        return None

    @property
    def uploader_name(self) -> Optional[str]:
        """Return the full name of the uploader."""
        return self.uploader.full_name if self.uploader else None

    @property
    def approver_name(self) -> Optional[str]:
        """Return the full name of the approver."""
        return self.approver.full_name if self.approver else None
