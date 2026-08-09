"""
ExamShield - Approval Workflow Service

Business logic orchestrating the multi-level approval pipeline.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import BadRequestException, NotFoundException, ForbiddenException
from app.models.approval_workflow import ApprovalDecision, ApprovalLevel, ApprovalWorkflow
from app.models.audit_log import AuditLog
from app.models.question_paper import QuestionPaperStatus
from app.repositories.approval_workflow_repository import ApprovalWorkflowRepository
from app.repositories.question_paper_repository import QuestionPaperRepository
from app.schemas.approval_workflow import (
    ApprovalDecisionRequest,
    ApprovalTimelineResponse,
    ApprovalWorkflowResponse,
)
from app.schemas.question_paper import QuestionPaperResponse
from app.services.notification_interface import NotificationService, PlaceholderNotificationService

logger = logging.getLogger("examshield.approval_service")


class ApprovalWorkflowService:
    """
    Service layer enforcing question paper approval rules.
    """

    def __init__(
        self,
        session: AsyncSession,
        notification_service: Optional[NotificationService] = None,
    ) -> None:
        self._session = session
        self._workflow_repo = ApprovalWorkflowRepository(session)
        self._paper_repo = QuestionPaperRepository(session)
        self._notifier = notification_service or PlaceholderNotificationService()

    def _to_workflow_response(self, stage: ApprovalWorkflow) -> ApprovalWorkflowResponse:
        return ApprovalWorkflowResponse.model_validate(stage)

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> None:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="workflows",
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    # ── Public API ───────────────────────────────────────────────

    async def submit_for_review(self, paper_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """
        Move a paper from UPLOADED/DRAFT to UNDER_REVIEW and create the first pending stage.
        Usually triggered automatically after upload by the Question Setter.
        """
        paper = await self._paper_repo.get_by_id(paper_id)
        if not paper:
            raise NotFoundException(f"Paper '{paper_id}' not found")

        # Create first stage: Moderator
        first_level = ApprovalLevel.MODERATOR
        
        # Check if already pending somewhere
        pending = await self._workflow_repo.get_current_pending_stage(paper_id)
        if pending:
            return  # Already submitted

        # Create pending stage
        stage = ApprovalWorkflow(
            question_paper_id=paper_id,
            approval_level=first_level,
            decision=ApprovalDecision.PENDING,
        )
        self._session.add(stage)
        
        # Update paper status
        await self._paper_repo.update(paper_id, {"status": QuestionPaperStatus.UNDER_REVIEW})
        
        await self._session.flush()
        
        await self._create_audit_entry(
            user_id=user_id,
            action="workflow_started",
            resource_id=str(paper_id),
            details={"initial_level": first_level}
        )

    async def get_timeline(self, paper_id: uuid.UUID) -> ApprovalTimelineResponse:
        """Get full timeline of a paper's approval process."""
        paper = await self._paper_repo.get_with_relations(paper_id)
        if not paper:
            raise NotFoundException(f"Paper '{paper_id}' not found")

        history = await self._workflow_repo.get_workflow_history(paper_id)
        pending_stage = await self._workflow_repo.get_current_pending_stage(paper_id)

        return ApprovalTimelineResponse(
            paper=QuestionPaperResponse.model_validate(paper),
            current_stage=pending_stage.approval_level if pending_stage else None,
            history=[self._to_workflow_response(h) for h in history],
        )

    async def list_pending_for_role(self, user_role: str) -> List[QuestionPaperResponse]:
        """List papers pending approval based on user role."""
        level_map = {
            "Moderator": ApprovalLevel.MODERATOR,
            "Controller": ApprovalLevel.CHIEF_CONTROLLER,
            "Admin": ApprovalLevel.EXAM_AUTHORITY,
        }
        target_level = level_map.get(user_role)
        if not target_level:
            return []  # Role has no approval authority
            
        papers = await self._workflow_repo.list_pending_approvals(target_level)
        return [QuestionPaperResponse.model_validate(p) for p in papers]

    async def process_decision(
        self,
        paper_id: uuid.UUID,
        request: ApprovalDecisionRequest,
        user_id: uuid.UUID,
        user_role: str,
        ip_address: Optional[str] = None,
    ) -> ApprovalTimelineResponse:
        """Process an approval, rejection, or return."""
        
        # 1. Validate Paper & Pending Stage
        paper = await self._paper_repo.get_by_id(paper_id)
        if not paper:
            raise NotFoundException(f"Paper '{paper_id}' not found")

        pending_stage = await self._workflow_repo.get_current_pending_stage(paper_id)
        if not pending_stage:
            raise BadRequestException("No pending approval stage for this paper")

        # 2. Validate Role Authorization
        level_map = {
            ApprovalLevel.MODERATOR: ["Moderator", "Admin"],
            ApprovalLevel.CHIEF_CONTROLLER: ["Controller", "Admin"],
            ApprovalLevel.EXAM_AUTHORITY: ["Admin", "Controller"],
        }
        allowed_roles = level_map.get(pending_stage.approval_level, ["Admin"])
        
        if user_role not in allowed_roles:
            raise ForbiddenException(f"Role '{user_role}' cannot approve '{pending_stage.approval_level}' stage")

        # 3. Update Current Stage
        await self._workflow_repo.update(
            pending_stage.id,
            {
                "decision": request.decision,
                "approver_id": user_id,
                "remarks": request.remarks,
                "approved_at": datetime.now(timezone.utc),
            }
        )

        # 4. Handle Decision Flow
        if request.decision == ApprovalDecision.APPROVED:
            current_idx = ApprovalLevel.ORDER.index(pending_stage.approval_level)
            is_final = current_idx == len(ApprovalLevel.ORDER) - 1
            
            if is_final:
                # Final approval
                await self._paper_repo.update(
                    paper_id, 
                    {"status": QuestionPaperStatus.APPROVED, "approved_by": user_id}
                )
            else:
                # Move to next stage
                next_level = ApprovalLevel.ORDER[current_idx + 1]
                new_stage = ApprovalWorkflow(
                    question_paper_id=paper_id,
                    approval_level=next_level,
                    decision=ApprovalDecision.PENDING,
                )
                self._session.add(new_stage)
                await self._notifier.notify_user(
                    paper.uploaded_by, 
                    "Paper Advanced", 
                    f"Paper {paper.paper_code} advanced to {next_level}"
                )

        elif request.decision == ApprovalDecision.REJECTED:
            # Paper is completely rejected
            await self._paper_repo.update(paper_id, {"status": QuestionPaperStatus.REJECTED})
            await self._notifier.notify_user(
                paper.uploaded_by, 
                "Paper Rejected", 
                f"Paper {paper.paper_code} was rejected at {pending_stage.approval_level}"
            )

        elif request.decision == ApprovalDecision.RETURNED:
            # Needs revision (stays under review or goes back to draft depending on policy; we keep it UNDER_REVIEW)
            await self._notifier.notify_user(
                paper.uploaded_by, 
                "Paper Returned", 
                f"Paper {paper.paper_code} was returned for revision by {pending_stage.approval_level}"
            )

        # 5. Audit Log
        await self._create_audit_entry(
            user_id=user_id,
            action=f"workflow_{request.decision}",
            resource_id=str(paper_id),
            details={
                "level": pending_stage.approval_level,
                "decision": request.decision,
                "remarks": request.remarks,
                "paper_code": paper.paper_code,
                "version": paper.version,
            },
            ip_address=ip_address,
        )

        await self._session.flush()
        
        return await self.get_timeline(paper_id)
