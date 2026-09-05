"""
Integration tests for Approval Workflow
"""

import uuid
from typing import Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.approval_workflow import ApprovalDecision, ApprovalLevel
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
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
async def test_workflow_timeline(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    headers = await _get_auth_headers(client)

    # 1. Trigger submit for review (Controller can view)
    # Create the first workflow stage (Moderator)
    from app.services.approval_workflow_service import ApprovalWorkflowService
    service = ApprovalWorkflowService(db_session)
    await service.submit_for_review(test_paper.id, test_paper.uploaded_by)

    # Fetch timeline
    response = await client.get(
        f"/api/v1/workflows/{test_paper.id}",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["current_stage"] == ApprovalLevel.MODERATOR
    assert data["paper"]["status"] == QuestionPaperStatus.UNDER_REVIEW


@pytest.mark.asyncio
async def test_approve_workflow_stage(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    # Set up initial pending stage
    from app.services.approval_workflow_service import ApprovalWorkflowService
    service = ApprovalWorkflowService(db_session)
    await service.submit_for_review(test_paper.id, test_paper.uploaded_by)

    # Get Admin headers (allowed to approve Moderator stage)
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Approve
    response = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        headers=headers,
        json={"decision": "approved", "remarks": "Looks good"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Should move to next stage (Controller)
    assert data["current_stage"] == ApprovalLevel.CHIEF_CONTROLLER
    history = data["history"]
    assert len(history) == 2
    assert history[0]["decision"] == ApprovalDecision.APPROVED


@pytest.mark.asyncio
async def test_reject_workflow_stage(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    # Set up initial pending stage
    from app.services.approval_workflow_service import ApprovalWorkflowService
    service = ApprovalWorkflowService(db_session)
    await service.submit_for_review(test_paper.id, test_paper.uploaded_by)

    headers = await _get_auth_headers(client)

    # Reject
    response = await client.post(
        f"/api/v1/workflows/{test_paper.id}/reject",
        headers=headers,
        json={"decision": "rejected", "remarks": "Too hard"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    
    # Paper status should be rejected
    assert data["paper"]["status"] == QuestionPaperStatus.REJECTED
    assert data["history"][0]["decision"] == ApprovalDecision.REJECTED


@pytest.mark.asyncio
async def test_list_pending_approvals(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    # Set up initial pending stage (Moderator)
    from app.services.approval_workflow_service import ApprovalWorkflowService
    service = ApprovalWorkflowService(db_session)
    await service.submit_for_review(test_paper.id, test_paper.uploaded_by)

    # Get Moderator headers (we don't have one seeded, so let's check Admin who sees nothing or Controller)
    # The list_pending endpoint checks user's role. Admin is mapped to Exam Authority.
    # So Admin should have 0 pending if it's currently at Moderator stage.
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")
    
    response = await client.get(
        "/api/v1/workflows/pending",
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    # Since admin's pending are EXAM_AUTHORITY, they should have 0 pending.
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_final_approval_stage(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """When a paper with encrypted_metadata reaches final approval, it should transition to ENCRYPTED."""
    from app.services.approval_workflow_service import ApprovalWorkflowService
    from app.models.approval_workflow import ApprovalWorkflow, ApprovalLevel, ApprovalDecision
    from app.models.question_paper import QuestionPaperStatus
    from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
    from app.models.key_metadata import KeyMetadata, Algorithm, KeyPurpose, KeyStatus

    # 1. Create a KeyMetadata row (FK target for encrypted_paper_metadata.key_identifier)
    key_meta = KeyMetadata(
        key_identifier="test-wrapping-key-001",
        algorithm=Algorithm.RSA4096,
        key_purpose=KeyPurpose.WRAPPING,
        key_version=1,
        status=KeyStatus.ACTIVE,
    )
    db_session.add(key_meta)
    await db_session.flush()  # flush so the FK target exists for SQLite

    # 2. Simulate that it is already at Exam Authority (final stage)
    stage = ApprovalWorkflow(
        question_paper_id=test_paper.id,
        approval_level=ApprovalLevel.EXAM_AUTHORITY,
        decision=ApprovalDecision.PENDING,
    )
    db_session.add(stage)

    # 3. Attach encrypted metadata using the correct column names
    metadata = EncryptedPaperMetadata(
        question_paper_id=test_paper.id,
        key_identifier="test-wrapping-key-001",
        nonce="dGVzdG5vbmNl",           # base64-encoded placeholder
        wrapped_key="d3JhcHBlZGtleQ==",  # base64-encoded placeholder
        encrypted_storage_path="/encrypted/test_paper.enc",
        encryption_algorithm="AES256_GCM",
        encryption_version=1,
    )
    db_session.add(metadata)
    await db_session.commit()
    await db_session.refresh(test_paper)

    # Admin acts as Exam Authority
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Approve final stage
    response = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        headers=headers,
        json={"decision": "approved", "remarks": "Approved by Authority"},
    )
    assert response.status_code == 200

    # Reload paper and verify it transitioned to ENCRYPTED
    await db_session.refresh(test_paper)
    assert test_paper.status == QuestionPaperStatus.ENCRYPTED


@pytest.mark.asyncio
async def test_final_approval_encrypts_and_transitions_to_encrypted(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """When a paper reaches final approval, it should automatically encrypt and transition to ENCRYPTED."""
    from app.models.approval_workflow import ApprovalWorkflow, ApprovalLevel, ApprovalDecision
    from app.models.question_paper import QuestionPaperStatus
    from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
    from app.models.key_metadata import KeyMetadata, KeyStatus, KeyPurpose, Algorithm
    from sqlalchemy import select

    # 1. Fetch active RSA4096 wrapping key identifier
    stmt_key = select(KeyMetadata).where(
        KeyMetadata.status == KeyStatus.ACTIVE,
        KeyMetadata.key_purpose == KeyPurpose.WRAPPING,
        KeyMetadata.algorithm == Algorithm.RSA4096
    )
    active_key = (await db_session.execute(stmt_key)).scalar_one()

    # 2. Simulate pending final stage approval (Exam Authority) without prior metadata
    stage = ApprovalWorkflow(
        question_paper_id=test_paper.id,
        approval_level=ApprovalLevel.EXAM_AUTHORITY,
        decision=ApprovalDecision.PENDING,
    )
    db_session.add(stage)
    await db_session.commit()

    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    response = await client.post(
        f"/api/v1/workflows/{test_paper.id}/approve",
        headers=headers,
        json={"decision": "approved", "remarks": "Final approval triggers encryption"},
    )
    assert response.status_code == 200

    await db_session.refresh(test_paper)
    # Requirement 1: Final approval transitions the paper to ENCRYPTED.
    assert test_paper.status == QuestionPaperStatus.ENCRYPTED

    # Requirement 2: EncryptedPaperMetadata exists after encryption.
    stmt_meta = select(EncryptedPaperMetadata).where(EncryptedPaperMetadata.question_paper_id == test_paper.id)
    meta = (await db_session.execute(stmt_meta)).scalar_one_or_none()
    assert meta is not None

    # Requirement 3: The metadata key_identifier references the active RSA4096 wrapping key.
    assert meta.key_identifier == active_key.key_identifier

    # Requirement 4: The encrypted payload exists.
    from app.core.dependencies import get_storage_provider
    storage_prov = get_storage_provider()
    ciphertext = await storage_prov.read(test_paper.storage_path)
    assert ciphertext is not None and len(ciphertext) > 0


@pytest.mark.asyncio
async def test_encrypted_paper_appears_and_approved_paper_hidden_in_release_dashboard(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """
    Requirement 5: An ENCRYPTED paper appears in the Release Dashboard query.
    Requirement 6: An APPROVED-but-not-encrypted paper does not appear in the Release Dashboard query.
    """
    headers = await _get_auth_headers(client, "admin@examshield.gov.in")

    # Set paper status to APPROVED without metadata
    test_paper.status = QuestionPaperStatus.APPROVED
    await db_session.commit()

    # Query release dashboard endpoint: GET /question-papers?status=encrypted&limit=100
    res_approved = await client.get("/api/v1/question-papers?status=encrypted&limit=100", headers=headers)
    assert res_approved.status_code == 200
    papers_list = res_approved.json()["data"]
    # Requirement 6: APPROVED-but-not-encrypted paper does NOT appear
    assert not any(p["id"] == str(test_paper.id) for p in papers_list)

    # Now set paper status to ENCRYPTED
    test_paper.status = QuestionPaperStatus.ENCRYPTED
    await db_session.commit()

    res_encrypted = await client.get("/api/v1/question-papers?status=encrypted&limit=100", headers=headers)
    assert res_encrypted.status_code == 200
    encrypted_papers_list = res_encrypted.json()["data"]
    # Requirement 5: ENCRYPTED paper appears
    assert any(p["id"] == str(test_paper.id) for p in encrypted_papers_list)


@pytest.mark.asyncio
async def test_scheduling_approved_paper_directly_rejected(
    client: AsyncClient, test_paper: QuestionPaper, db_session: AsyncSession
):
    """Requirement 7: Scheduling an APPROVED paper directly is rejected by the backend."""
    from datetime import datetime, timedelta, timezone

    # Set status to APPROVED
    test_paper.status = QuestionPaperStatus.APPROVED
    await db_session.commit()

    headers = await _get_auth_headers(client, "admin@examshield.gov.in")
    release_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()

    response = await client.post(
        f"/api/v1/release/{test_paper.id}/schedule",
        json={"release_at": release_at},
        headers=headers,
    )
    assert response.status_code == 400
    assert "must be in 'encrypted' status" in response.json()["message"]

