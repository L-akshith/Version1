"""
ExamShield - Key Metadata Model

Tracks cryptographic key lifecycle and metadata without storing secret materials.
"""

import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Enum,
    Integer,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin, UUIDMixin


class Algorithm(str, enum.Enum):
    AES256_GCM = "AES256_GCM"
    RSA4096 = "RSA4096"
    ECC_P256 = "ECC_P256"
    Ed25519 = "Ed25519"


class KeyPurpose(str, enum.Enum):
    ENCRYPTION = "Encryption"
    SIGNATURE = "Signature"
    VERIFICATION = "Verification"
    WRAPPING = "Wrapping"


class KeyStatus(str, enum.Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    EXPIRED = "Expired"
    REVOKED = "Revoked"


class KeyMetadata(UUIDMixin, TimestampMixin, Base):
    """
    Metadata representation of a cryptographic key stored in an external KMS.
    """
    __tablename__ = "key_metadata"

    key_identifier: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    
    algorithm: Mapped[Algorithm] = mapped_column(String(50), nullable=False)
    key_purpose: Mapped[KeyPurpose] = mapped_column(String(50), nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    status: Mapped[KeyStatus] = mapped_column(String(20), default=KeyStatus.INACTIVE, index=True, nullable=False)
    
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rotation_due: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)

    def __repr__(self) -> str:
        return f"<KeyMetadata(identifier='{self.key_identifier}', version={self.key_version}, status='{self.status}')>"
