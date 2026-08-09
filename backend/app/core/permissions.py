"""
ExamShield - Permission System

Provides a flexible permission checker that can be used as a FastAPI dependency
to protect routes based on role permissions.
"""

from enum import Enum
from typing import List

from fastapi import Depends, HTTPException, status


class Resource(str, Enum):
    """Enumeration of protected resources in the system."""

    USERS = "users"
    ROLES = "roles"
    PERMISSIONS = "permissions"
    PAPERS = "papers"
    AUDIT = "audit"
    SYSTEM = "system"


class Action(str, Enum):
    """Enumeration of actions that can be performed on resources."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    MANAGE = "manage"
    APPROVE = "approve"
    RELEASE = "release"
    INVESTIGATE = "investigate"


# ── Default Permission Definitions ───────────────────────────────
# These are the base permissions that will be seeded into the database.

DEFAULT_PERMISSIONS = [
    # User management
    {"name": "users:create", "resource": Resource.USERS, "action": Action.CREATE, "description": "Create new users"},
    {"name": "users:read", "resource": Resource.USERS, "action": Action.READ, "description": "View user details"},
    {"name": "users:update", "resource": Resource.USERS, "action": Action.UPDATE, "description": "Update user information"},
    {"name": "users:delete", "resource": Resource.USERS, "action": Action.DELETE, "description": "Delete users"},
    {"name": "users:list", "resource": Resource.USERS, "action": Action.LIST, "description": "List all users"},
    {"name": "users:manage", "resource": Resource.USERS, "action": Action.MANAGE, "description": "Full user management"},
    # Role management
    {"name": "roles:create", "resource": Resource.ROLES, "action": Action.CREATE, "description": "Create new roles"},
    {"name": "roles:read", "resource": Resource.ROLES, "action": Action.READ, "description": "View role details"},
    {"name": "roles:update", "resource": Resource.ROLES, "action": Action.UPDATE, "description": "Update roles"},
    {"name": "roles:delete", "resource": Resource.ROLES, "action": Action.DELETE, "description": "Delete roles"},
    {"name": "roles:list", "resource": Resource.ROLES, "action": Action.LIST, "description": "List all roles"},
    {"name": "roles:manage", "resource": Resource.ROLES, "action": Action.MANAGE, "description": "Full role management"},
    # Paper management
    {"name": "papers:create", "resource": Resource.PAPERS, "action": Action.CREATE, "description": "Upload examination papers"},
    {"name": "papers:read", "resource": Resource.PAPERS, "action": Action.READ, "description": "View examination papers"},
    {"name": "papers:update", "resource": Resource.PAPERS, "action": Action.UPDATE, "description": "Update examination papers"},
    {"name": "papers:delete", "resource": Resource.PAPERS, "action": Action.DELETE, "description": "Delete examination papers"},
    {"name": "papers:list", "resource": Resource.PAPERS, "action": Action.LIST, "description": "List examination papers"},
    {"name": "papers:approve", "resource": Resource.PAPERS, "action": Action.APPROVE, "description": "Approve examination papers"},
    {"name": "papers:release", "resource": Resource.PAPERS, "action": Action.RELEASE, "description": "Release examination papers"},
    # Audit
    {"name": "audit:read", "resource": Resource.AUDIT, "action": Action.READ, "description": "View audit logs"},
    {"name": "audit:list", "resource": Resource.AUDIT, "action": Action.LIST, "description": "List audit entries"},
    # System
    {"name": "system:manage", "resource": Resource.SYSTEM, "action": Action.MANAGE, "description": "System administration"},
    # Investigation
    {"name": "papers:investigate", "resource": Resource.PAPERS, "action": Action.INVESTIGATE, "description": "Investigate paper leaks"},
]

# ── Default Roles and their Permissions ──────────────────────────

DEFAULT_ROLES = {
    "Admin": {
        "description": "Full system administrator with unrestricted access",
        "permissions": [p["name"] for p in DEFAULT_PERMISSIONS],
    },
    "Controller": {
        "description": "Examination controller overseeing paper lifecycle",
        "permissions": [
            "users:list", "users:read",
            "roles:list", "roles:read",
            "papers:create", "papers:read", "papers:update", "papers:list",
            "papers:approve", "papers:release",
            "audit:read", "audit:list",
        ],
    },
    "Question Setter": {
        "description": "Subject matter expert who creates examination questions",
        "permissions": [
            "papers:create", "papers:read", "papers:update", "papers:list",
        ],
    },
    "Translation Officer": {
        "description": "Translates examination papers into regional languages",
        "permissions": [
            "papers:read", "papers:update", "papers:list",
        ],
    },
    "Moderator": {
        "description": "Reviews and moderates examination papers for quality",
        "permissions": [
            "papers:read", "papers:list", "papers:approve",
        ],
    },
    "Exam Center Officer": {
        "description": "Manages paper distribution at examination centers",
        "permissions": [
            "papers:read", "papers:list",
        ],
    },
    "Observer": {
        "description": "Read-only observer for audit and compliance",
        "permissions": [
            "papers:list", "papers:read",
            "audit:read", "audit:list",
        ],
    },
    "Investigator": {
        "description": "Investigates potential paper leaks and security incidents",
        "permissions": [
            "papers:read", "papers:list", "papers:investigate",
            "audit:read", "audit:list",
            "users:list", "users:read",
        ],
    },
}


class PermissionChecker:
    """
    FastAPI dependency that checks whether the current user
    has the required permissions.

    Usage:
        @router.get("/papers", dependencies=[Depends(PermissionChecker(["papers:list"]))])
        async def list_papers(...):
            ...
    """

    def __init__(self, required_permissions: List[str]) -> None:
        self.required_permissions = required_permissions

    async def __call__(self, current_user: "User" = None) -> bool:  # noqa: F821
        """
        Validate that the current user has all required permissions.

        The actual User dependency injection is wired in dependencies.py
        to avoid circular imports. This class is used by the dependency
        factory in core/dependencies.py.
        """
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )

        if current_user.is_superuser:
            return True

        if current_user.role is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No role assigned to user",
            )

        user_permissions = {p.name for p in current_user.role.permissions}

        missing = set(self.required_permissions) - user_permissions
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(sorted(missing))}",
            )

        return True
