"""
ExamShield - Audit Schemas

Pydantic v2 schemas for audit log query and response payloads.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AuditLogResponse(BaseModel):
    """Schema for audit log entry response."""

    id: uuid.UUID = Field(..., description="Audit log entry UUID")
    user_id: Optional[uuid.UUID] = Field(
        default=None, description="User who performed the action"
    )
    action: str = Field(..., description="Action performed")
    resource: str = Field(..., description="Resource type")
    resource_id: Optional[str] = Field(
        default=None, description="Resource identifier"
    )
    details: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional details"
    )
    ip_address: Optional[str] = Field(
        default=None, description="Client IP address"
    )
    user_agent: Optional[str] = Field(
        default=None, description="Client user agent"
    )
    status_code: Optional[int] = Field(
        default=None, description="HTTP status code"
    )
    endpoint: Optional[str] = Field(
        default=None, description="API endpoint"
    )
    execution_time_ms: Optional[float] = Field(
        default=None, description="Request execution time in milliseconds"
    )
    created_at: datetime = Field(..., description="Timestamp of the action")

    model_config = {"from_attributes": True}


class AuditLogQuery(BaseModel):
    """Schema for querying audit logs."""

    user_id: Optional[uuid.UUID] = Field(
        default=None, description="Filter by user ID"
    )
    action: Optional[str] = Field(
        default=None, description="Filter by action"
    )
    resource: Optional[str] = Field(
        default=None, description="Filter by resource"
    )
    start_date: Optional[datetime] = Field(
        default=None, description="Filter entries after this date"
    )
    end_date: Optional[datetime] = Field(
        default=None, description="Filter entries before this date"
    )
    skip: int = Field(default=0, ge=0, description="Pagination offset")
    limit: int = Field(default=50, ge=1, le=500, description="Pagination limit")
