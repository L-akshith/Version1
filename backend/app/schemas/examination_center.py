"""
ExamShield - Examination Center Schemas
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ExaminationCenterCreate(BaseModel):
    center_code: str = Field(..., min_length=2, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)


class ExaminationCenterResponse(BaseModel):
    id: uuid.UUID
    center_code: str
    name: str
    status: str
    public_key_pem: Optional[str] = None
    key_identifier: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class KeyProvisionRequest(BaseModel):
    public_key_pem: str = Field(..., description="RSA Public Key in PEM format")
    key_identifier: str = Field(..., description="Unique identifier for this key version")
