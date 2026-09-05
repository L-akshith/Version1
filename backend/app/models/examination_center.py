"""
ExamShield - Examination Center Model

Defines the ExaminationCenter ORM model representing physical or logical
locations authorized to receive and decrypt examination materials.
"""

from typing import List, Optional

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin
from app.models.exam_center_association import ExamCenterAssociation


class CenterStatus:
    """Allowed status values for an examination center."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"


class ExaminationCenter(UUIDMixin, TimestampMixin, Base):
    """
    Examination Center model representing authorized locations.
    Stores the center's public key used for securely wrapping
    AES session keys during the release phase.
    """

    __tablename__ = "examination_centers"

    center_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=CenterStatus.ACTIVE,
        index=True,
    )
    public_key_pem: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    key_identifier: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    exams: Mapped[List["Exam"]] = relationship(
        "Exam",
        secondary=ExamCenterAssociation.__table__,
        back_populates="authorized_centers",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<ExaminationCenter(id={self.id}, code='{self.center_code}', status='{self.status}')>"
