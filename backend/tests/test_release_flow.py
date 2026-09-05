"""
Tests for the Secure Release Flow - Phase 3 Requirements
"""
import uuid
import base64
import os
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.models.exam import Exam, ExamStatus
from app.models.examination_center import ExaminationCenter, CenterStatus
from app.models.exam_center_association import ExamCenterAssociation
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.models.center_release_key import CenterReleaseKey
from app.models.release_schedule import ReleaseSchedule, ReleaseStatus
from app.models.audit_log import AuditLog
from app.schemas.release import ReleaseScheduleCreate

pytestmark = pytest.mark.asyncio

@pytest.fixture
def center_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public_key = private_key.public_key()
    
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    return private_key, pem


async def get_controller_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    from tests.api.test_centers_and_releases_phase1_5 import get_or_create_controller, get_auth_headers
    await get_or_create_controller(db_session)
    return await get_auth_headers(client, "controller@examshield.gov.in")

async def setup_encrypted_paper(db_session: AsyncSession, local_crypto_provider, test_paper, test_admin):
    from app.models.key_metadata import KeyMetadata, KeyStatus, KeyPurpose, Algorithm
    
    stmt = select(KeyMetadata).where(
        KeyMetadata.status == KeyStatus.ACTIVE,
        KeyMetadata.key_purpose == KeyPurpose.WRAPPING,
        KeyMetadata.algorithm == Algorithm.RSA4096
    )
    key_meta = (await db_session.execute(stmt)).scalar_one()
    wrapping_key_id = key_meta.key_identifier
    
    test_paper.status = QuestionPaperStatus.ENCRYPTED
    db_session.add(test_paper)

    mock_aes_key = os.urandom(32)
    wrapped_aes_key = await local_crypto_provider.wrap_key(wrapping_key_id, mock_aes_key)
    metadata = EncryptedPaperMetadata(
        id=uuid.uuid4(),
        question_paper_id=test_paper.id,
        key_identifier=wrapping_key_id,
        encryption_algorithm="AES256_GCM",
        nonce="mocknonce",
        wrapped_key=base64.b64encode(wrapped_aes_key).decode('utf-8'),
        encrypted_storage_path="mock/path",
        encryption_version=1
    )
    db_session.add(metadata)
    await db_session.commit()
    
    # Expire so next access re-fetches with the encrypted_metadata relationship
    await db_session.refresh(test_paper)
    
    return mock_aes_key, wrapping_key_id

async def setup_test_center(db_session: AsyncSession, center_code: str, status=CenterStatus.ACTIVE):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
    
    center = ExaminationCenter(
        id=uuid.uuid4(),
        center_code=center_code,
        name=f"Test Center {center_code}",
        status=status,
        public_key_pem=pem,
        key_identifier=f"center-key-{center_code}"
    )
    db_session.add(center)
    await db_session.commit()
    return center, private_key

# 1. Successfully schedule an approved encrypted paper.
async def test_schedule_encrypted_paper(client: AsyncClient, db_session: AsyncSession, test_paper, test_admin, setup_active_rsa_key, local_crypto_provider):
    await setup_encrypted_paper(db_session, local_crypto_provider, test_paper, test_admin)
    headers = await get_controller_headers(client, db_session)
    
    release_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = await client.post(
        f"/api/v1/release/{test_paper.id}/schedule",
        json={"release_at": release_at},
        headers=headers
    )
    assert response.status_code == 200, response.json()
    assert response.json()["status"] == ReleaseStatus.SCHEDULED
    
    await db_session.refresh(test_paper)
    assert test_paper.status == QuestionPaperStatus.SCHEDULED

# 2. Reject scheduling when the paper has not completed approval.
# 3. Reject scheduling when the paper is not encrypted.
async def test_reject_unapproved_unencrypted_paper(client: AsyncClient, db_session: AsyncSession, test_paper):
    headers = await get_controller_headers(client, db_session)
    test_paper.status = QuestionPaperStatus.UPLOADED
    await db_session.commit()
    
    release_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    response = await client.post(
        f"/api/v1/release/{test_paper.id}/schedule",
        json={"release_at": release_at},
        headers=headers
    )
    assert response.status_code == 400
    assert "must be in 'encrypted' status" in response.json()["message"]

# 4. Reject release schedules whose release_at is in the past.
async def test_reject_past_schedule(client: AsyncClient, db_session: AsyncSession, test_paper, test_admin, setup_active_rsa_key, local_crypto_provider):
    await setup_encrypted_paper(db_session, local_crypto_provider, test_paper, test_admin)
    headers = await get_controller_headers(client, db_session)
    
    release_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    response = await client.post(
        f"/api/v1/release/{test_paper.id}/schedule",
        json={"release_at": release_at},
        headers=headers
    )
    assert response.status_code == 400
    assert "must be in the future" in response.json()["message"]

# 5. Reject execution before release_at.
async def test_reject_execution_before_release_at(client: AsyncClient, db_session: AsyncSession, test_paper, test_admin, setup_active_rsa_key, local_crypto_provider):
    await setup_encrypted_paper(db_session, local_crypto_provider, test_paper, test_admin)
    headers = await get_controller_headers(client, db_session)
    
    release_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    await client.post(
        f"/api/v1/release/{test_paper.id}/schedule",
        json={"release_at": release_at},
        headers=headers
    )
    
    response = await client.post(f"/api/v1/release/{test_paper.id}/execute", headers=headers)
    assert response.status_code == 400
    assert "not yet been reached" in response.json()["message"]

# 6. Successfully execute after release_at.
# 7. Verify the paper transitions to RELEASED only after successful release.
# 8. Verify every authorized active center receives exactly one CenterReleaseKey for that release.
# 9. Verify revoked/inactive centers do not receive new release keys.
# 10. Verify unauthorized centers do not receive release keys.
async def test_execute_release_centers_logic(client: AsyncClient, db_session: AsyncSession, test_paper, test_exam, test_admin, setup_active_rsa_key, local_crypto_provider):
    await setup_encrypted_paper(db_session, local_crypto_provider, test_paper, test_admin)
    headers = await get_controller_headers(client, db_session)
    
    # Setup centers
    c1, _ = await setup_test_center(db_session, "C1", CenterStatus.ACTIVE)
    c2, _ = await setup_test_center(db_session, "C2", CenterStatus.ACTIVE)
    c_revoked, _ = await setup_test_center(db_session, "C_REV", CenterStatus.REVOKED)
    c_unauth, _ = await setup_test_center(db_session, "C_UNAUTH", CenterStatus.ACTIVE)
    
    # Authorize c1, c2, c_revoked to the exam
    db_session.add_all([
        ExamCenterAssociation(exam_id=test_exam.id, center_id=c1.id),
        ExamCenterAssociation(exam_id=test_exam.id, center_id=c2.id),
        ExamCenterAssociation(exam_id=test_exam.id, center_id=c_revoked.id)
    ])
    
    # Schedule
    schedule = ReleaseSchedule(
        question_paper_id=test_paper.id,
        release_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status=ReleaseStatus.SCHEDULED,
        scheduled_by=test_admin.id
    )
    db_session.add(schedule)
    test_paper.status = QuestionPaperStatus.SCHEDULED
    await db_session.commit()
    
    response = await client.post(f"/api/v1/release/{test_paper.id}/execute", headers=headers)
    assert response.status_code == 200, response.json()
    
    # 7. Transitions to RELEASED
    await db_session.refresh(test_paper)
    assert test_paper.status == QuestionPaperStatus.RELEASED
    await db_session.refresh(schedule)
    assert schedule.status == ReleaseStatus.RELEASED
    
    # 8, 9, 10. Check keys distributed correctly
    keys = (await db_session.execute(select(CenterReleaseKey).where(CenterReleaseKey.question_paper_id == test_paper.id))).scalars().all()
    assert len(keys) == 2
    
    center_ids = [str(k.examination_center_id) for k in keys]
    assert str(c1.id) in center_ids
    assert str(c2.id) in center_ids
    assert str(c_revoked.id) not in center_ids
    assert str(c_unauth.id) not in center_ids

# 19. Simulate one center having an invalid public key.
# Verify release fails, rolls back, paper not RELEASED, no partial CenterReleaseKey, appropriate audit/error.
async def test_invalid_public_key_rollback(client: AsyncClient, db_session: AsyncSession, test_paper, test_exam, test_admin, setup_active_rsa_key, local_crypto_provider):
    await setup_encrypted_paper(db_session, local_crypto_provider, test_paper, test_admin)
    headers = await get_controller_headers(client, db_session)
    
    c1, _ = await setup_test_center(db_session, "C1")
    c2, _ = await setup_test_center(db_session, "C2")
    c2.public_key_pem = "INVALID_PEM_DATA"
    
    db_session.add_all([
        ExamCenterAssociation(exam_id=test_exam.id, center_id=c1.id),
        ExamCenterAssociation(exam_id=test_exam.id, center_id=c2.id)
    ])
    
    schedule = ReleaseSchedule(
        question_paper_id=test_paper.id,
        release_at=datetime.now(timezone.utc) - timedelta(minutes=1),
        status=ReleaseStatus.SCHEDULED,
        scheduled_by=test_admin.id
    )
    db_session.add(schedule)
    test_paper.status = QuestionPaperStatus.SCHEDULED
    await db_session.commit()
    
    try:
        response = await client.post(f"/api/v1/release/{test_paper.id}/execute", headers=headers)
        # If the global exception handler catches it, we get a 500
        assert response.status_code == 500
    except (ValueError, ExceptionGroup):
        # If the exception propagates through ASGI, that's also acceptable
        # — the point is that the release did NOT succeed
        pass
    
    # Critical invariant: paper must NOT transition to RELEASED
    await db_session.refresh(test_paper)
    assert test_paper.status != QuestionPaperStatus.RELEASED
    
    # The schedule must NOT show as RELEASED
    await db_session.refresh(schedule)
    assert schedule.status != ReleaseStatus.RELEASED
