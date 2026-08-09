"""
ExamShield - Authentication Tests

Tests user registration, login, JWT issuance, profile retrieval,
and access control exceptions.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.models.user import User

pytestmark = pytest.mark.asyncio


async def test_register_user_success(client: AsyncClient, db_session) -> None:
    """Verify that a user can register successfully with valid details."""
    payload = {
        "email": "testuser@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Test User",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["message"] == "User registered successfully"
    assert json_data["data"]["email"] == payload["email"]
    assert json_data["data"]["full_name"] == payload["full_name"]
    assert "id" in json_data["data"]
    
    # Confirm user exists in the DB
    stmt = select(User).where(User.email == payload["email"])
    result = await db_session.execute(stmt)
    user = result.scalar_one_or_none()
    assert user is not None
    assert user.full_name == "Test User"


async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Verify registration fails if email is already taken."""
    payload = {
        "email": "duplicate@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "User One",
    }
    
    # Register once
    response1 = await client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201
    
    # Register twice
    response2 = await client.post("/api/v1/auth/register", json=payload)
    assert response2.status_code == 409
    assert response2.json()["success"] is False
    assert "already registered" in response2.json()["message"]


async def test_login_success(client: AsyncClient) -> None:
    """Verify successful login returns valid JWT tokens."""
    # First register
    reg_payload = {
        "email": "login@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Login User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)
    
    # Now login
    login_payload = {
        "email": "login@examshield.gov.in",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert "access_token" in json_data["data"]
    assert "refresh_token" in json_data["data"]
    assert json_data["data"]["token_type"] == "bearer"


async def test_login_invalid_credentials(client: AsyncClient) -> None:
    """Verify login fails with wrong credentials."""
    login_payload = {
        "email": "nonexistent@examshield.gov.in",
        "password": "WrongPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert response.json()["success"] is False


async def test_get_me_success(client: AsyncClient) -> None:
    """Verify profile retrieval using valid bearer token."""
    reg_payload = {
        "email": "me@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Me User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)
    
    # Login to get token
    login_payload = {
        "email": "me@examshield.gov.in",
        "password": "SecurePassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    token = login_res.json()["data"]["access_token"]
    
    # Call me endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_res = await client.get("/api/v1/auth/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["success"] is True
    assert me_res.json()["data"]["email"] == reg_payload["email"]


async def test_get_me_unauthorized(client: AsyncClient) -> None:
    """Verify profile request fails without token or with invalid token."""
    # No Authorization header → HTTPBearer returns 403
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403

    # Invalid token → JWT decode fails → 401
    headers = {"Authorization": "Bearer invalidtokenhere"}
    response2 = await client.get("/api/v1/auth/me", headers=headers)
    assert response2.status_code == 401

