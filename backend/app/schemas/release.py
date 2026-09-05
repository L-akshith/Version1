"""
ExamShield - Release Schemas
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReleaseScheduleCreate(BaseModel):
    release_at: datetime = Field(..., description="UTC timestamp for release execution")


class ReleaseScheduleResponse(BaseModel):
    id: uuid.UUID
    question_paper_id: uuid.UUID
    release_at: datetime
    status: str
    scheduled_by: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ReleasePackage(BaseModel):
    question_paper_id: uuid.UUID
    version: int
    encryption_algorithm: str
    nonce: str
    wrapped_key: str
    sha256_hash: str
    encrypted_artifact_path: str
