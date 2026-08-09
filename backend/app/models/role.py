"""
ExamShield - Role Model

Defines the Role ORM model and the role_permissions association table
for the many-to-many relationship between roles and permissions.
"""

import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, ForeignKey, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.permission import Permission
    from app.models.user import User

# ── Association Table ────────────────────────────────────────────
role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column(
        "role_id",
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "permission_id",
        UUID(as_uuid=True),
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Role(UUIDMixin, TimestampMixin, Base):
    """
    Role model for role-based access control.

    Each role has a unique name and can be associated with multiple
    permissions through the role_permissions association table.
    """

    __tablename__ = "roles"

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

    # ── Relationships ────────────────────────────────────────────
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission",
        secondary=role_permissions,
        back_populates="roles",
        lazy="selectin",
    )
    users: Mapped[List["User"]] = relationship(
        "User",
        back_populates="role",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Role(id={self.id}, name='{self.name}')>"

    def has_permission(self, permission_name: str) -> bool:
        """Check if this role has a specific permission."""
        return any(p.name == permission_name for p in self.permissions)
