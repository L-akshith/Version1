"""
ExamShield - Approval Workflow Schemas

Pydantic schemas for the approval workflow module.
"""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.approval_workflow import ApprovalDecision
from app.schemas.question_paper import QuestionPaperResponse


class ApprovalDecisionRequest(BaseModel):
    """Schema for submitting an approval decision."""

    decision: str = Field(
        ...,
        description="The decision made (approved, rejected, returned)",
    )
    remarks: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Optional remarks/comments by the approver",
    )


class ApprovalWorkflowResponse(BaseModel):
    """Schema for an individual workflow stage response."""

    id: uuid.UUID = Field(..., description="Workflow stage UUID")
    question_paper_id: uuid.UUID = Field(..., description="Paper UUID")
    approval_level: str = Field(..., description="Level in the hierarchy")
    approver_id: Optional[uuid.UUID] = Field(default=None, description="Approver UUID")
    approver_name: Optional[str] = Field(default=None, description="Approver full name")
    decision: str = Field(..., description="Decision made (or pending)")
    remarks: Optional[str] = Field(default=None, description="Remarks")
    approved_at: Optional[datetime] = Field(default=None, description="Decision timestamp")
    created_at: datetime = Field(..., description="Stage creation timestamp")

    model_config = {"from_attributes": True}


class ApprovalTimelineResponse(BaseModel):
    """Schema for the full timeline of a question paper."""

    paper: QuestionPaperResponse = Field(..., description="Question paper metadata")
    current_stage: Optional[str] = Field(default=None, description="Current pending stage")
    history: List[ApprovalWorkflowResponse] = Field(..., description="Complete workflow history ordered chronologically")
