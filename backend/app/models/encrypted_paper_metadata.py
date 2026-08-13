"""
ExamShield - Encrypted Paper Metadata Model

Defines the EncryptedPaperMetadata ORM model, which persistently links a
QuestionPaper to its encrypted artifact and stores the cryptographic
attributes (wrapped key, nonce, algorithm) required for decryption.
"""

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin


class EncryptedPaperMetadata(UUIDMixin, TimestampMixin, Base):
    """
    Persistent metadata for an encrypted question paper.

    Stores the RSA-wrapped AES session key, the AES-GCM nonce, and the
    path to the encrypted artifact. It does NOT store the plaintext paper,
    the RSA private key, or the plaintext AES key.
    """

    __tablename__ = "encrypted_paper_metadata"

    question_paper_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("question_papers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    
    key_identifier: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )
    
    encryption_algorithm: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="AES256_GCM",
    )
    
    nonce: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    wrapped_key: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    
    encrypted_storage_path: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )
    
    encryption_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    # ── Relationships ────────────────────────────────────────────
    question_paper: Mapped["QuestionPaper"] = relationship(
        "QuestionPaper",
        back_populates="encrypted_metadata",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<EncryptedPaperMetadata(id={self.id}, "
            f"paper_id={self.question_paper_id}, "
            f"algorithm='{self.encryption_algorithm}')>"
        )
