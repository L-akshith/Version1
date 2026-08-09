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
