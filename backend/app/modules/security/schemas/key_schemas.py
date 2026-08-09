"""
ExamShield - Security Key Schemas
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.key_metadata import Algorithm, KeyPurpose, KeyStatus


class KeyMetadataResponse(BaseModel):
    """Schema for returning key metadata to clients."""
    id: uuid.UUID
    key_identifier: str
    algorithm: Algorithm
    key_purpose: KeyPurpose
    key_version: int
    status: KeyStatus
    expires_at: Optional[datetime] = None
    activated_at: Optional[datetime] = None
    deactivated_at: Optional[datetime] = None
    rotation_due: Optional[datetime] = None
    created_by: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GenerateKeyRequest(BaseModel):
    """Schema for requesting generation of a new cryptographic key."""
    algorithm: Algorithm
    key_purpose: KeyPurpose
