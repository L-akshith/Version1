"""
ExamShield - Audit Log Model

Tracks all significant actions in the system for compliance and
forensic investigation purposes.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, UUIDMixin


class AuditLog(UUIDMixin, Base):
    """
    Audit log model for tracking system activity.

    Every significant action (login, paper access, role change, etc.)
    is recorded here with full context for forensic analysis.
    """

    __tablename__ = "audit_logs"

    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )
    resource_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    details: Mapped[Optional[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        default=dict,
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    user_agent: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    status_code: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    endpoint: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )
    execution_time_ms: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, action='{self.action}', "
            f"resource='{self.resource}')>"
        )
