"""
ExamShield - Question Paper Schemas

Pydantic v2 schemas for question paper request/response payloads
including upload metadata, update operations, and statistics.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class QuestionPaperUpload(BaseModel):
    """Schema for question paper upload metadata (sent as Form fields)."""

    subject_id: uuid.UUID = Field(
        ...,
        description="UUID of the parent subject",
    )
    paper_code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Unique paper code within the subject (e.g., PHY-SET-A)",
    )
    title: str = Field(
        ...,
        min_length=2,
        max_length=255,
        description="Title of the question paper",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the paper",
    )

    @field_validator("paper_code")
    @classmethod
    def validate_paper_code_format(cls, v: str) -> str:
        """Normalize paper code to uppercase and strip whitespace."""
        return v.strip().upper()


class QuestionPaperUpdate(BaseModel):
    """Schema for updating question paper metadata."""

    title: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
        description="Updated title",
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Updated description",
    )
    status: Optional[str] = Field(
        default=None,
        description="New status (must follow valid transition rules)",
    )


class QuestionPaperResponse(BaseModel):
    """Schema for question paper response data."""

    id: uuid.UUID = Field(..., description="Paper UUID")
    subject_id: uuid.UUID = Field(..., description="Parent subject UUID")
    paper_code: str = Field(..., description="Paper code")
    title: str = Field(..., description="Paper title")
    version: int = Field(..., description="Version number")
    description: Optional[str] = Field(default=None, description="Description")
    status: str = Field(..., description="Current lifecycle status")
    file_name: str = Field(..., description="System-generated filename")
    original_file_name: str = Field(..., description="Original upload filename")
    storage_path: str = Field(..., description="Storage location path")
    mime_type: str = Field(..., description="File MIME type")
    file_size: int = Field(..., description="File size in bytes")
    sha256_hash: str = Field(..., description="SHA-256 integrity hash")
    uploaded_by: uuid.UUID = Field(..., description="Uploader user UUID")
    approved_by: Optional[uuid.UUID] = Field(default=None, description="Approver user UUID")
    upload_time: datetime = Field(..., description="Upload timestamp")
    subject_name: Optional[str] = Field(default=None, description="Parent subject name")
    exam_name: Optional[str] = Field(default=None, description="Parent exam name")
    uploader_name: Optional[str] = Field(default=None, description="Uploader full name")
    approver_name: Optional[str] = Field(default=None, description="Approver full name")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class QuestionPaperVersionResponse(BaseModel):
    """Schema for version history entries."""

    id: uuid.UUID = Field(..., description="Paper UUID")
    version: int = Field(..., description="Version number")
    status: str = Field(..., description="Status")
    file_name: str = Field(..., description="System filename")
    original_file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    sha256_hash: str = Field(..., description="SHA-256 hash")
    uploaded_by: uuid.UUID = Field(..., description="Uploader UUID")
    uploader_name: Optional[str] = Field(default=None, description="Uploader name")
    upload_time: datetime = Field(..., description="Upload timestamp")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = {"from_attributes": True}


class QuestionPaperStatistics(BaseModel):
    """Schema for question paper dashboard statistics."""

    total: int = Field(default=0, description="Total number of papers")
    draft: int = Field(default=0, description="Number of draft papers")
    uploaded: int = Field(default=0, description="Number of uploaded papers")
    under_review: int = Field(default=0, description="Number of papers under review")
    approved: int = Field(default=0, description="Number of approved papers")
    rejected: int = Field(default=0, description="Number of rejected papers")
    archived: int = Field(default=0, description="Number of archived papers")
