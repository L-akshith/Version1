"""
ExamShield - Exam Schemas

Pydantic v2 schemas for exam-related request/response payloads.
"""

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class ExamCreate(BaseModel):
    """Schema for creating a new examination."""

    exam_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique exam code (e.g., NEET-2026-M1)",
    )
    exam_name: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Full name of the examination",
    )
    conducting_authority: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Authority conducting the exam (e.g., NTA, UPSC, SSC)",
    )
    year: int = Field(
        ...,
        ge=2000,
        le=2100,
        description="Examination year",
    )
    exam_date: date = Field(
        ...,
        description="Date of the examination",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the examination",
    )

    @field_validator("exam_code")
    @classmethod
    def validate_exam_code_format(cls, v: str) -> str:
        """Normalize exam code to uppercase and strip whitespace."""
        return v.strip().upper()


class ExamUpdate(BaseModel):
    """Schema for updating an existing examination."""

    exam_name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Full name of the examination",
    )
    conducting_authority: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Authority conducting the exam",
    )
    year: Optional[int] = Field(
        default=None,
        ge=2000,
        le=2100,
        description="Examination year",
    )
    exam_date: Optional[date] = Field(
        default=None,
        description="Date of the examination",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the examination",
    )
    status: Optional[str] = Field(
        default=None,
        description="New status (must follow valid transition rules)",
    )


class ExamResponse(BaseModel):
    """Schema for exam response data."""

    id: uuid.UUID = Field(..., description="Exam UUID")
    exam_code: str = Field(..., description="Unique exam code")
    exam_name: str = Field(..., description="Full examination name")
    conducting_authority: str = Field(..., description="Conducting authority")
    year: int = Field(..., description="Examination year")
    exam_date: date = Field(..., description="Examination date")
    description: Optional[str] = Field(default=None, description="Description")
    status: str = Field(..., description="Current lifecycle status")
    created_by: uuid.UUID = Field(..., description="Creator user UUID")
    creator_name: Optional[str] = Field(default=None, description="Creator full name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class ExamStatistics(BaseModel):
    """Schema for exam dashboard statistics."""

    total: int = Field(default=0, description="Total number of exams")
    draft: int = Field(default=0, description="Number of draft exams")
    scheduled: int = Field(default=0, description="Number of scheduled exams")
    active: int = Field(default=0, description="Number of active exams")
    completed: int = Field(default=0, description="Number of completed exams")
    archived: int = Field(default=0, description="Number of archived exams")
