"""
ExamShield - Center Release Key Model

Defines the CenterReleaseKey ORM model. Stores the AES session key for a
QuestionPaper, securely wrapped with a specific Examination Center's public key.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, UUIDMixin


class CenterReleaseKey(UUIDMixin, Base):
    """
    Stores the AES session key wrapped for a specific center.
    This guarantees isolated key distribution.
    """

    __tablename__ = "center_release_keys"

    examination_center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("examination_centers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    wrapped_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    key_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # ── Relationships ────────────────────────────────────────────
    examination_center: Mapped["ExaminationCenter"] = relationship(
        "ExaminationCenter",
        lazy="selectin",
    )
    question_paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<CenterReleaseKey(id={self.id}, center_id={self.examination_center_id}, "
            f"paper_id={self.question_paper_id})>"
        )
