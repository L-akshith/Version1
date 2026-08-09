"""
ExamShield - Repository Layer Tests

Tests generic BaseRepository capabilities and User-specific database operations.
"""

import pytest
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role
from app.repositories.user_repository import UserRepository
from app.repositories.role_repository import RoleRepository

pytestmark = pytest.mark.asyncio


async def test_user_repository_crud(db_session) -> None:
    """Verify standard CRUD capabilities of UserRepository."""
    user_repo = UserRepository(db_session)
    role_repo = RoleRepository(db_session)
    
    # Verify we can find a role
    observer_role = await role_repo.get_by_name("Observer")
    assert observer_role is not None
    
    # Create user
    user_data = {
        "email": "repo_test@examshield.gov.in",
        "hashed_password": "some_hashed_string",
        "full_name": "Repository Test User",
        "is_active": True,
        "role_id": observer_role.id,
    }
    
    user = await user_repo.create(user_data)
    assert user.id is not None
    assert user.email == user_data["email"]
    assert user.role_id == observer_role.id
    
    # Retrieve user
    retrieved = await user_repo.get_by_id(user.id)
    assert retrieved is not None
    assert retrieved.email == user.email
    
    # Get user with role eagerly loaded
    retrieved_with_role = await user_repo.get_with_role(user.id)
    assert retrieved_with_role is not None
    assert retrieved_with_role.role is not None
    assert retrieved_with_role.role.name == "Observer"
    
    # Check email exists check
    assert await user_repo.email_exists(user_data["email"]) is True
    assert await user_repo.email_exists("notfound@examshield.gov.in") is False
    
    # Update user
    updated = await user_repo.update(user.id, {"full_name": "Updated Name"})
    assert updated is not None
    assert updated.full_name == "Updated Name"
    
    # Check list users
    users = await user_repo.get_all(skip=0, limit=10)
    assert len(users) >= 2  # Superuser + repo_test user
    
    # Delete user
    deleted = await user_repo.delete(user.id)
    assert deleted is True
    
    # Verify no longer exists
    assert await user_repo.exists(user.id) is False


async def test_role_repository_permissions(db_session) -> None:
    """Verify permission association updates in RoleRepository."""
    role_repo = RoleRepository(db_session)
    
    # Retrieve Admin role
    admin_role = await role_repo.get_by_name("Admin")
    assert admin_role is not None
    
    # Verify admin has permissions
    assert len(admin_role.permissions) > 0
    assert admin_role.has_permission("users:manage") is True
    
    # Test adding a permission that already exists on a different role
    observer_role = await role_repo.get_by_name("Observer")
    assert observer_role is not None
    
    # Find any permission observer doesn't have, e.g., "users:manage"
    admin_perms = {p.name: p for p in admin_role.permissions}
    manage_perm = admin_perms["users:manage"]
    
    # Observer should not have users:manage initially
    assert observer_role.has_permission("users:manage") is False
    
    # Add permission
    updated_observer = await role_repo.add_permission(observer_role.id, manage_perm.id)
    assert updated_observer is not None
    assert updated_observer.has_permission("users:manage") is True
    
    # Remove permission
    removed_observer = await role_repo.remove_permission(observer_role.id, manage_perm.id)
    assert removed_observer is not None
    assert removed_observer.has_permission("users:manage") is False
