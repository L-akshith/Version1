import uuid
from datetime import datetime, timezone, timedelta
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.examination_center import ExaminationCenter, CenterStatus
from app.models.release_schedule import ReleaseSchedule, ReleaseStatus
from app.models.exam_center_association import ExamCenterAssociation

pytestmark = pytest.mark.asyncio

async def create_test_center(db_session: AsyncSession, center_code: str = "CTR001") -> ExaminationCenter:
    center = ExaminationCenter(
        id=uuid.uuid4(),
        center_code=center_code,
        name="Test Center",
        status=CenterStatus.ACTIVE,
        public_key_pem="-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA3Q==\n-----END PUBLIC KEY-----",
        key_identifier="key-123"
    )
    db_session.add(center)
    await db_session.commit()
    return center

async def create_test_schedule(db_session: AsyncSession, paper_id: uuid.UUID, user_id: uuid.UUID) -> ReleaseSchedule:
    schedule = ReleaseSchedule(
        id=uuid.uuid4(),
        question_paper_id=paper_id,
        release_at=datetime.now(timezone.utc) + timedelta(days=1),
        status=ReleaseStatus.SCHEDULED,
        scheduled_by=user_id,
    )
    db_session.add(schedule)
    await db_session.commit()
    return schedule

async def get_auth_headers(client: AsyncClient, email: str, password: str = "ChangeThisPassword123!") -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password}
    )
    assert response.status_code == 200, f"Login failed for {email}"
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

from app.models.user import User
from app.models.role import Role
from sqlalchemy import select
from app.utils.password import hash_password

async def get_or_create_controller(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "controller@examshield.gov.in")
    user = (await db_session.execute(stmt)).scalar_one_or_none()
    if user:
        return user
        
    role_stmt = select(Role).where(Role.name == "Controller")
    role = (await db_session.execute(role_stmt)).scalar_one()
    
    user = User(
        email="controller@examshield.gov.in",
        hashed_password=hash_password("ChangeThisPassword123!"),
        full_name="Test Controller",
        is_active=True,
        is_superuser=False,
        role_id=role.id
    )
    db_session.add(user)
    await db_session.commit()
    return user

async def test_get_centers_authorization(client: AsyncClient, test_admin, db_session: AsyncSession):
    # Without token
    response = await client.get("/api/v1/centers")
    assert response.status_code in (401, 403)
    
    # As controller (doesn't have system:manage)
    await get_or_create_controller(db_session)
    headers = await get_auth_headers(client, "controller@examshield.gov.in")
    response = await client.get("/api/v1/centers", headers=headers)
    assert response.status_code == 403

async def test_get_centers_response(client: AsyncClient, db_session: AsyncSession):
    await create_test_center(db_session)
    headers = await get_auth_headers(client, "admin@examshield.gov.in")
    response = await client.get("/api/v1/centers", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    
    # Assert private keys / raw sensitive data are not exposed
    # Schema should only return what's in ExaminationCenterResponse
    center = data["data"][0]
    assert "id" in center
    assert "center_code" in center
    assert "name" in center
    assert "status" in center
    assert "public_key_pem" in center
    assert "key_identifier" in center
    # No private key exists in model anyway, but this verifies schema
    assert "private_key" not in center

async def test_get_release_schedules_authorization(client: AsyncClient):
    response = await client.get("/api/v1/release/schedules/upcoming")
    assert response.status_code in (401, 403)

async def test_get_release_schedules_response(client: AsyncClient, db_session: AsyncSession, test_paper, test_admin):
    await create_test_schedule(db_session, test_paper.id, test_admin.id)
    
    # As controller (has papers:release)
    await get_or_create_controller(db_session)
    headers = await get_auth_headers(client, "controller@examshield.gov.in")
    response = await client.get("/api/v1/release/schedules/upcoming", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) >= 1
    
    schedule = data["data"][0]
    assert "id" in schedule
    assert "question_paper_id" in schedule
    assert "release_at" in schedule
    assert "status" in schedule
    assert "scheduled_by" in schedule
    # Make sure we don't expose raw AES keys here
    assert "aes_key" not in schedule
    assert "wrapped_key" not in schedule

async def test_center_deactivation_authorization(client: AsyncClient, db_session: AsyncSession):
    center = await create_test_center(db_session, center_code="CTR002")
    
    # As controller (unauthorized)
    await get_or_create_controller(db_session)
    headers = await get_auth_headers(client, "controller@examshield.gov.in")
    response = await client.post(f"/api/v1/centers/{center.id}/deactivate", headers=headers)
    assert response.status_code == 403

async def test_center_deactivation_state_change(client: AsyncClient, db_session: AsyncSession):
    center = await create_test_center(db_session, center_code="CTR003")
    assert center.status == CenterStatus.ACTIVE
    
    headers = await get_auth_headers(client, "admin@examshield.gov.in")
    response = await client.post(f"/api/v1/centers/{center.id}/deactivate", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == CenterStatus.REVOKED
    
    # Ensure audit event was created
    from sqlalchemy import select
    from app.models.audit_log import AuditLog
    stmt = select(AuditLog).where(AuditLog.resource_id == str(center.id), AuditLog.action == "center_revoked")
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is not None

async def test_revoked_center_cannot_participate_in_new_release(client: AsyncClient, db_session: AsyncSession, test_paper, test_exam, test_admin):
    # We will simulate a release execution where the center is revoked
    center = await create_test_center(db_session, center_code="CTR004")
    
    # Authorize center for exam
    assoc = ExamCenterAssociation(exam_id=test_exam.id, center_id=center.id)
    db_session.add(assoc)
    await db_session.commit()
    
    # Revoke it
    headers = await get_auth_headers(client, "admin@examshield.gov.in")
    await client.post(f"/api/v1/centers/{center.id}/deactivate", headers=headers)
    
    # Change paper status to ENCRYPTED so it can be scheduled
    from app.models.question_paper import QuestionPaperStatus
    test_paper.status = QuestionPaperStatus.ENCRYPTED
    db_session.add(test_paper)
    
    from app.models.key_metadata import KeyMetadata, KeyPurpose, Algorithm, KeyStatus
    from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
    
    key_meta = KeyMetadata(
        id=uuid.uuid4(),
        key_identifier="test-rsa-key-xxx",
        key_purpose=KeyPurpose.WRAPPING,
        algorithm=Algorithm.RSA4096,
        status=KeyStatus.ACTIVE,
        created_by=test_admin.id
    )
    db_session.add(key_meta)
    await db_session.commit()
    
    metadata = EncryptedPaperMetadata(
        id=uuid.uuid4(),
        question_paper_id=test_paper.id,
        encryption_algorithm="AES256_GCM",
        nonce="fake",
        wrapped_key="fake_b64==",
        key_identifier="test-rsa-key-xxx",
        encrypted_storage_path="local/fake.enc"
    )
    db_session.add(metadata)
    test_paper.encrypted_metadata = metadata
    await db_session.commit()
    
    # Schedule release manually to bypass the "must be in future" validation
    from app.models.release_schedule import ReleaseSchedule, ReleaseStatus
    
    schedule = ReleaseSchedule(
        question_paper_id=test_paper.id,
        release_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status=ReleaseStatus.SCHEDULED,
        scheduled_by=test_admin.id
    )
    db_session.add(schedule)
    test_paper.status = QuestionPaperStatus.SCHEDULED
    await db_session.commit()
    
    await get_or_create_controller(db_session)
    controller_headers = await get_auth_headers(client, "controller@examshield.gov.in")
    from unittest.mock import patch
    
    # Try to execute release
    with patch("app.modules.security.providers.local_crypto_provider.LocalCryptoKeyProvider.unwrap_key", return_value=b"fake_aes_key"):
        exec_resp = await client.post(
            f"/api/v1/release/{test_paper.id}/execute",
            headers=controller_headers
        )
    
    # Should fail because no ACTIVE centers are found (our only center is revoked)
    assert exec_resp.status_code == 400
    assert "No active authorized examination centers" in exec_resp.json()["message"]

async def test_historical_release_records_remain_intact(client: AsyncClient, db_session: AsyncSession, test_paper, test_exam):
    center = await create_test_center(db_session, center_code="CTR005")
    
    # Authorize center for exam
    assoc = ExamCenterAssociation(exam_id=test_exam.id, center_id=center.id)
    db_session.add(assoc)
    
    # Create a historical release key record manually
    from app.models.center_release_key import CenterReleaseKey
    old_key = CenterReleaseKey(
        id=uuid.uuid4(),
        examination_center_id=center.id,
        question_paper_id=test_paper.id,
        wrapped_key="old_wrapped_key",
        key_identifier="key-old",
    )
    db_session.add(old_key)
    await db_session.commit()
    
    # Revoke center
    headers = await get_auth_headers(client, "admin@examshield.gov.in")
    response = await client.post(f"/api/v1/centers/{center.id}/deactivate", headers=headers)
    assert response.status_code == 200
    
    # Verify historical record still exists
    from sqlalchemy import select
    stmt = select(CenterReleaseKey).where(CenterReleaseKey.id == old_key.id)
    result = await db_session.execute(stmt)
    assert result.scalar_one_or_none() is not None
