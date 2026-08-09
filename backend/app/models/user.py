"""
ExamShield - User Model

Defines the User ORM model with authentication fields, role assignment,
and activity tracking.
"""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.role import Role


class User(UUIDMixin, TimestampMixin, Base):
    """
    User model for authentication and authorization.

    Each user has a unique email address, a hashed password,
    and is assigned exactly one role for RBAC.
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # ── Foreign Keys ─────────────────────────────────────────────
    role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # ── Relationships ────────────────────────────────────────────
    role: Mapped[Optional["Role"]] = relationship(
        "Role",
        back_populates="users",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}')>"

    @property
    def role_name(self) -> Optional[str]:
        """Return the name of the user's role, or None if unassigned."""
        return self.role.name if self.role else None

    @property
    def permission_names(self) -> set[str]:
        """Return the set of permission names available to this user."""
        if self.is_superuser:
            return {"*"}
        if self.role is None:
            return set()
        return {p.name for p in self.role.permissions}
