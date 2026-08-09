"""
ExamShield - User Management Tests

Tests user updates, deactivation, role assignments, pagination,
and permission guards.
"""

import pytest
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User
from app.models.role import Role

pytestmark = pytest.mark.asyncio


async def _get_superuser_headers(client: AsyncClient) -> dict:
    """Helper to authenticate as superuser and return headers."""
    login_payload = {
        "email": "admin@examshield.gov.in",
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_list_users_as_admin(client: AsyncClient) -> None:
    """Verify admin can list all registered users."""
    headers = await _get_superuser_headers(client)
    
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert len(json_data["data"]) >= 1
    assert any(u["email"] == "admin@examshield.gov.in" for u in json_data["data"])


async def test_list_users_forbidden_for_regular_user(client: AsyncClient) -> None:
    """Verify non-admin/regular user cannot list users."""
    # Register and login regular user (default role is Observer, lacks users:list)
    reg_payload = {
        "email": "regular@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Regular User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)
    
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "regular@examshield.gov.in",
        "password": "SecurePassword123!",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    response = await client.get("/api/v1/users", headers=headers)
    assert response.status_code == 403  # Forbidden


async def test_deactivate_and_activate_user(client: AsyncClient, db_session) -> None:
    """Verify superuser can deactivate and activate user accounts."""
    admin_headers = await _get_superuser_headers(client)
    
    # Create user
    reg_payload = {
        "email": "lifecycle@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Lifecycle User",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    user_id = reg_res.json()["data"]["id"]
    
    # Deactivate user
    deact_res = await client.put(f"/api/v1/users/{user_id}/deactivate", headers=admin_headers)
    assert deact_res.status_code == 200
    assert deact_res.json()["data"]["is_active"] is False
    
    # Re-fetch user in db
    db_session.expire_all()
    stmt = select(User).where(User.id == uuid.UUID(user_id))
    res = await db_session.execute(stmt)
    user = res.scalar_one()
    assert user.is_active is False
    
    # Deactivated user login should fail
    login_payload = {
        "email": "lifecycle@examshield.gov.in",
        "password": "SecurePassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["message"]
    
    # Reactivate user
    act_res = await client.put(f"/api/v1/users/{user_id}/activate", headers=admin_headers)
    assert act_res.status_code == 200
    assert act_res.json()["data"]["is_active"] is True
    
    # Now login should succeed again
    login_res2 = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res2.status_code == 200


async def test_assign_user_role(client: AsyncClient, db_session) -> None:
    """Verify administrator can assign different roles to users."""
    admin_headers = await _get_superuser_headers(client)
    
    # Register regular user
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "to_promote@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "To Promote",
    })
    user_id = reg_res.json()["data"]["id"]
    assert reg_res.json()["data"]["role_name"] == "Observer"
    
    # Find Investigator role ID
    stmt = select(Role).where(Role.name == "Investigator")
    res = await db_session.execute(stmt)
    investigator_role = res.scalar_one()
    
    # Assign Investigator role
    assign_res = await client.put(
        f"/api/v1/users/{user_id}/role",
        json={"role_id": str(investigator_role.id)},
        headers=admin_headers,
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["data"]["role_name"] == "Investigator"
    
    # Log in as the new Investigator user and access Investigator-guarded route
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "to_promote@examshield.gov.in",
        "password": "SecurePassword123!",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # List audit logs requires audit:list or roles with papers:investigate
    # The investigator role has papers:investigate, and audit:list
    audit_res = await client.get("/api/v1/audit/logs", headers=headers)
    assert audit_res.status_code == 200
