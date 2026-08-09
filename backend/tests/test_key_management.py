"""
Integration tests for Security Key Lifecycle Management
"""

import uuid
from typing import Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.key_metadata import KeyMetadata, KeyPurpose, KeyStatus, Algorithm
from app.models.user import User


async def _get_auth_headers(client: AsyncClient, email: str = "admin@examshield.gov.in") -> Dict[str, str]:
    """Authenticate and return authorization headers."""
    login_payload = {
        "email": email,
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200, f"Login failed for {email}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_generate_key(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    response = await client.post(
        "/api/v1/security/keys",
        headers=headers,
        json={"algorithm": Algorithm.AES256_GCM.value, "key_purpose": KeyPurpose.ENCRYPTION.value},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    
    assert data["algorithm"] == Algorithm.AES256_GCM.value
    assert data["key_purpose"] == KeyPurpose.ENCRYPTION.value
    assert data["status"] == KeyStatus.INACTIVE.value
    assert data["key_version"] == 1


@pytest.mark.asyncio
async def test_activate_key(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    # Generate
    gen_response = await client.post(
        "/api/v1/security/keys",
        headers=headers,
        json={"algorithm": Algorithm.AES256_GCM.value, "key_purpose": KeyPurpose.ENCRYPTION.value},
    )
    key_id = gen_response.json()["data"]["id"]

    # Activate
    act_response = await client.post(
        f"/api/v1/security/keys/{key_id}/activate",
        headers=headers,
    )
    assert act_response.status_code == 200
    data = act_response.json()["data"]
    
    assert data["status"] == KeyStatus.ACTIVE.value
    assert data["activated_at"] is not None


@pytest.mark.asyncio
async def test_deactivate_key(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    # Generate & Activate
    gen_res = await client.post(
        "/api/v1/security/keys",
        headers=headers,
        json={"algorithm": Algorithm.AES256_GCM.value, "key_purpose": KeyPurpose.ENCRYPTION.value},
    )
    key_id = gen_res.json()["data"]["id"]
    await client.post(f"/api/v1/security/keys/{key_id}/activate", headers=headers)

    # Deactivate
    deact_response = await client.post(
        f"/api/v1/security/keys/{key_id}/deactivate",
        headers=headers,
    )
    assert deact_response.status_code == 200
    data = deact_response.json()["data"]
    
    assert data["status"] == KeyStatus.INACTIVE.value
    assert data["deactivated_at"] is not None


@pytest.mark.asyncio
async def test_rotate_key(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    # Generate & Activate
    gen_res = await client.post(
        "/api/v1/security/keys",
        headers=headers,
        json={"algorithm": Algorithm.AES256_GCM.value, "key_purpose": KeyPurpose.ENCRYPTION.value},
    )
    key_id = gen_res.json()["data"]["id"]
    await client.post(f"/api/v1/security/keys/{key_id}/activate", headers=headers)

    # Rotate
    rot_response = await client.post(
        f"/api/v1/security/keys/{key_id}/rotate",
        headers=headers,
    )
    assert rot_response.status_code == 200
    data = rot_response.json()["data"]
    
    # Provider mock returns version 2
    assert data["key_version"] == 2
    assert data["id"] != key_id

    # Verify old key is inactive
    old_key_res = await client.get(f"/api/v1/security/keys/{key_id}", headers=headers)
    assert old_key_res.json()["data"]["status"] == KeyStatus.INACTIVE.value


@pytest.mark.asyncio
async def test_list_keys(
    client: AsyncClient, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    # Generate a key
    await client.post(
        "/api/v1/security/keys",
        headers=headers,
        json={"algorithm": Algorithm.AES256_GCM.value, "key_purpose": KeyPurpose.ENCRYPTION.value},
    )

    # List
    list_res = await client.get("/api/v1/security/keys", headers=headers)
    assert list_res.status_code == 200
    data = list_res.json()["data"]
    
    assert len(data) >= 1
    assert data[0]["key_purpose"] == KeyPurpose.ENCRYPTION.value
