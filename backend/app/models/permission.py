"""
ExamShield - Permission Model

Defines the Permission ORM model representing granular access control
permissions that can be assigned to roles.
"""

from typing import TYPE_CHECKING, List

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.role import Role


class Permission(UUIDMixin, TimestampMixin, Base):
    """
    Permission model for granular access control.

    Each permission represents a specific action on a specific resource.
    Format: "resource:action" (e.g., "papers:create", "users:delete")
    """

    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        default="",
    )
    resource: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    roles: Mapped[List["Role"]] = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Permission(id={self.id}, name='{self.name}')>"
