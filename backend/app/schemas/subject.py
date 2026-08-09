"""
ExamShield - Subject Schemas

Pydantic v2 schemas for subject-related request/response payloads.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class SubjectCreate(BaseModel):
    """Schema for creating a new subject within an exam."""

    exam_id: uuid.UUID = Field(
        ...,
        description="UUID of the parent examination",
    )
    subject_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique subject code within the exam (e.g., PHY, CHEM, BIO)",
    )
    subject_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the subject (e.g., Physics, Chemistry)",
    )
    language: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Language of the subject (e.g., English, Hindi)",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the subject",
    )

    @field_validator("subject_code")
    @classmethod
    def validate_subject_code_format(cls, v: str) -> str:
        """Normalize subject code to uppercase and strip whitespace."""
        return v.strip().upper()


class SubjectUpdate(BaseModel):
    """Schema for updating an existing subject."""

    subject_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Full name of the subject",
    )
    language: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=50,
        description="Language of the subject",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the subject",
    )
    status: Optional[str] = Field(
        default=None,
        description="New status (must follow valid transition rules)",
    )


class SubjectResponse(BaseModel):
    """Schema for subject response data."""

    id: uuid.UUID = Field(..., description="Subject UUID")
    exam_id: uuid.UUID = Field(..., description="Parent exam UUID")
    subject_code: str = Field(..., description="Unique subject code within exam")
    subject_name: str = Field(..., description="Full subject name")
    language: str = Field(..., description="Subject language")
    description: Optional[str] = Field(default=None, description="Description")
    status: str = Field(..., description="Current lifecycle status")
    created_by: uuid.UUID = Field(..., description="Creator user UUID")
    exam_name: Optional[str] = Field(default=None, description="Parent exam name")
    creator_name: Optional[str] = Field(default=None, description="Creator full name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class SubjectListResponse(BaseModel):
    """Schema for subject list items (alias for SubjectResponse)."""

    id: uuid.UUID = Field(..., description="Subject UUID")
    exam_id: uuid.UUID = Field(..., description="Parent exam UUID")
    subject_code: str = Field(..., description="Unique subject code within exam")
    subject_name: str = Field(..., description="Full subject name")
    language: str = Field(..., description="Subject language")
    status: str = Field(..., description="Current lifecycle status")
    exam_name: Optional[str] = Field(default=None, description="Parent exam name")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class SubjectStatistics(BaseModel):
    """Schema for subject dashboard statistics."""

    total: int = Field(default=0, description="Total number of subjects")
    draft: int = Field(default=0, description="Number of draft subjects")
    active: int = Field(default=0, description="Number of active subjects")
    archived: int = Field(default=0, description="Number of archived subjects")
