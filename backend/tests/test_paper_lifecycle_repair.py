"""
ExamShield - Question Paper Lifecycle & Status Repair Tests

Regression tests for:
1. Approval workflow completion resulting in ENCRYPTED status.
2. Repairing APPROVED paper with valid EncryptedPaperMetadata to ENCRYPTED status.
3. Rejecting repair when encryption metadata is missing.
4. Rejecting repair when encryption metadata is incomplete.
5. Rejecting invalid lifecycle status transitions.
6. Preventing generic metadata edits from modifying locked/encrypted papers.
7. Audit log creation for repair without sensitive data leaks.
"""

import uuid
from typing import Dict
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_workflow import ApprovalDecision, ApprovalLevel
from app.models.audit_log import AuditLog
from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
from app.services.approval_workflow_service import ApprovalWorkflowService
from app.services.question_paper_service import QuestionPaperService


async def _get_auth_headers(
    client: AsyncClient, email: str = "admin@examshield.gov.in"
) -> Dict[str, str]:
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
async def test_successful_approval_workflow_ends_with_status_encrypted(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that complete approval pipeline ends with paper status ENCRYPTED."""
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")
    workflow_service = ApprovalWorkflowService(db_session)

    # 1. Submit for review -> UNDER_REVIEW
    await workflow_service.submit_for_review(test_paper.id, test_paper.uploaded_by)

    # 2. Stage 1 approval (Moderator)
    res_mod = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        json={"decision": "approved", "remarks": "Looks good"},
        headers=headers,
    )
    assert res_mod.status_code == 200, res_mod.text

    # 3. Stage 2 approval (Chief Controller)
    res_ctrl = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        json={"decision": "approved", "remarks": "Controller approved"},
        headers=headers,
    )
    assert res_ctrl.status_code == 200, res_ctrl.text

    # 4. Stage 3 approval (Exam Authority - Final)
    res_final = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        json={"decision": "approved", "remarks": "Final approval"},
        headers=headers,
    )
    assert res_final.status_code == 200, res_final.text

    # Check final status
    await db_session.refresh(test_paper)
    assert test_paper.status == QuestionPaperStatus.ENCRYPTED


@pytest.mark.asyncio
async def test_approved_paper_with_valid_metadata_repaired_to_encrypted(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that an APPROVED paper with existing valid EncryptedPaperMetadata can be repaired."""
    from app.models.key_metadata import KeyMetadata, KeyStatus
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Fetch active key metadata for valid foreign key reference
    key_stmt = select(KeyMetadata).where(KeyMetadata.status == KeyStatus.ACTIVE)
    active_key = (await db_session.execute(key_stmt)).scalars().first()
    key_id = active_key.key_identifier if active_key else "default-key-id"

    # Create valid EncryptedPaperMetadata
    metadata = EncryptedPaperMetadata(
        id=uuid.uuid4(),
        question_paper_id=test_paper.id,
        key_identifier=key_id,
        encryption_algorithm="AES256_GCM",
        nonce="dGVzdG5vbmNl",
        wrapped_key="dGVzdHdyYXBwZWRrZXk=",
        encrypted_storage_path="encrypted/test/paper.enc",
        encryption_version=1,
    )
    db_session.add(metadata)
    test_paper.status = QuestionPaperStatus.APPROVED
    await db_session.commit()

    # Call repair endpoint
    res = await client.post(
        f"/api/v1/question-papers/{test_paper.id}/repair-encryption-status",
        headers=headers,
    )
    assert res.status_code == 200, res.text
    data = res.json()["data"]
    assert data["status"] == QuestionPaperStatus.ENCRYPTED

    await db_session.refresh(test_paper)
    assert test_paper.status == QuestionPaperStatus.ENCRYPTED

    # Verify audit log was created
    stmt = (
        select(AuditLog)
        .where(
            AuditLog.resource_id == str(test_paper.id),
            AuditLog.action == "paper_encryption_status_repaired",
        )
    )
    audit_res = await db_session.execute(stmt)
    audit_entry = audit_res.scalar_one_or_none()
    assert audit_entry is not None
    assert audit_entry.details["previous_status"] == QuestionPaperStatus.APPROVED
    assert audit_entry.details["new_status"] == QuestionPaperStatus.ENCRYPTED
    # Ensure zero secret leakage in audit details
    details_str = str(audit_entry.details).lower()
    assert "wrapped_key" not in details_str
    assert "nonce" not in details_str
    assert "plaintext" not in details_str


@pytest.mark.asyncio
async def test_repair_fails_without_encryption_metadata(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that repair fails if EncryptedPaperMetadata is missing."""
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Ensure no metadata exists and set status to APPROVED
    if test_paper.encrypted_metadata:
        await db_session.delete(test_paper.encrypted_metadata)
    test_paper.status = QuestionPaperStatus.APPROVED
    await db_session.commit()

    res = await client.post(
        f"/api/v1/question-papers/{test_paper.id}/repair-encryption-status",
        headers=headers,
    )
    assert res.status_code == 400
    assert "Encrypted paper metadata is missing" in res.json()["message"]


@pytest.mark.asyncio
async def test_repair_fails_with_incomplete_encryption_metadata(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that repair fails if encryption metadata fields are incomplete."""
    from app.models.key_metadata import KeyMetadata, KeyStatus
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    key_stmt = select(KeyMetadata).where(KeyMetadata.status == KeyStatus.ACTIVE)
    active_key = (await db_session.execute(key_stmt)).scalars().first()
    key_id = active_key.key_identifier if active_key else "default-key-id"

    # Create incomplete EncryptedPaperMetadata (empty nonce)
    metadata = EncryptedPaperMetadata(
        id=uuid.uuid4(),
        question_paper_id=test_paper.id,
        key_identifier=key_id,
        encryption_algorithm="AES256_GCM",
        nonce="",  # Incomplete!
        wrapped_key="dGVzdHdyYXBwZWRrZXk=",
        encrypted_storage_path="encrypted/test/paper.enc",
        encryption_version=1,
    )
    db_session.add(metadata)
    test_paper.status = QuestionPaperStatus.APPROVED
    await db_session.commit()

    res = await client.post(
        f"/api/v1/question-papers/{test_paper.id}/repair-encryption-status",
        headers=headers,
    )
    assert res.status_code == 400
    assert "Encryption metadata is incomplete" in res.json()["message"]


@pytest.mark.asyncio
async def test_invalid_lifecycle_transitions_rejected(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that invalid status transitions are rejected."""
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Try transitioning UPLOADED directly to RELEASED
    test_paper.status = QuestionPaperStatus.UPLOADED
    await db_session.commit()

    res = await client.put(
        f"/api/v1/question-papers/{test_paper.id}",
        json={"status": QuestionPaperStatus.RELEASED},
        headers=headers,
    )
    assert res.status_code == 400
    assert "Invalid status transition" in res.json()["message"]


@pytest.mark.asyncio
async def test_locked_papers_cannot_be_edited_via_update(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Test that generic metadata edits on ENCRYPTED papers are rejected."""
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    test_paper.status = QuestionPaperStatus.ENCRYPTED
    await db_session.commit()

    res = await client.put(
        f"/api/v1/question-papers/{test_paper.id}",
        json={"title": "Unauthorized Title Edit"},
        headers=headers,
    )
    assert res.status_code == 400
    assert "It is locked" in res.json()["message"]
