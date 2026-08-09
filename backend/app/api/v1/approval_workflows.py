"""
ExamShield - Approval Workflow API Routes

Endpoints for managing question paper approvals.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import CurrentUser, get_approval_workflow_service, require_permissions
from app.models.approval_workflow import ApprovalDecision
from app.schemas.approval_workflow import ApprovalDecisionRequest, ApprovalTimelineResponse
from app.schemas.question_paper import QuestionPaperResponse
from app.schemas.response import APIResponse
from app.services.approval_workflow_service import ApprovalWorkflowService

router = APIRouter(tags=["Approval Workflow"])


@router.get(
    "/workflows/pending",
    response_model=APIResponse[list[QuestionPaperResponse]],
    summary="List pending approvals",
    dependencies=[Depends(require_permissions(["workflow:view"]))],
)
async def list_pending_approvals(
    current_user: CurrentUser,
    service: Annotated[ApprovalWorkflowService, Depends(get_approval_workflow_service)],
) -> APIResponse[list[QuestionPaperResponse]]:
    """List papers pending approval by the current user's role."""
    papers = await service.list_pending_for_role(current_user.role_name or "")
    return APIResponse.ok(data=papers)


@router.get(
    "/workflows/{paper_id}",
    response_model=APIResponse[ApprovalTimelineResponse],
    summary="Get workflow timeline",
    dependencies=[Depends(require_permissions(["workflow:view"]))],
)
async def get_workflow_timeline(
    paper_id: uuid.UUID,
    service: Annotated[ApprovalWorkflowService, Depends(get_approval_workflow_service)],
) -> APIResponse[ApprovalTimelineResponse]:
    """Get the full approval timeline for a paper."""
    timeline = await service.get_timeline(paper_id)
    return APIResponse.ok(data=timeline)


@router.post(
    "/workflows/{paper_id}/approve",
    response_model=APIResponse[ApprovalTimelineResponse],
    summary="Approve paper",
    dependencies=[Depends(require_permissions(["workflow:approve"]))],
)
async def approve_paper(
    paper_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    decision_req: ApprovalDecisionRequest,
    service: Annotated[ApprovalWorkflowService, Depends(get_approval_workflow_service)],
) -> APIResponse[ApprovalTimelineResponse]:
    """Approve a paper at the current stage."""
    decision_req.decision = ApprovalDecision.APPROVED
    timeline = await service.process_decision(
        paper_id=paper_id,
        request=decision_req,
        user_id=current_user.id,
        user_role=current_user.role_name or "",
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=timeline, message="Paper approved successfully")


@router.post(
    "/workflows/{paper_id}/reject",
    response_model=APIResponse[ApprovalTimelineResponse],
    summary="Reject paper",
    dependencies=[Depends(require_permissions(["workflow:reject"]))],
)
async def reject_paper(
    paper_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    decision_req: ApprovalDecisionRequest,
    service: Annotated[ApprovalWorkflowService, Depends(get_approval_workflow_service)],
) -> APIResponse[ApprovalTimelineResponse]:
    """Reject a paper outright."""
    decision_req.decision = ApprovalDecision.REJECTED
    timeline = await service.process_decision(
        paper_id=paper_id,
        request=decision_req,
        user_id=current_user.id,
        user_role=current_user.role_name or "",
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=timeline, message="Paper rejected successfully")


@router.post(
    "/workflows/{paper_id}/return",
    response_model=APIResponse[ApprovalTimelineResponse],
    summary="Return paper",
    dependencies=[Depends(require_permissions(["workflow:return"]))],
)
async def return_paper(
    paper_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    decision_req: ApprovalDecisionRequest,
    service: Annotated[ApprovalWorkflowService, Depends(get_approval_workflow_service)],
) -> APIResponse[ApprovalTimelineResponse]:
    """Return a paper for revision."""
    decision_req.decision = ApprovalDecision.RETURNED
    timeline = await service.process_decision(
        paper_id=paper_id,
        request=decision_req,
        user_id=current_user.id,
        user_role=current_user.role_name or "",
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=timeline, message="Paper returned for revision")
