"""
ExamShield - Audit Log API Routes

Endpoints for querying the audit trail.
"""

import uuid
from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import require_permissions, get_async_session
from app.database.session import get_async_session
from app.models.audit_log import AuditLog
from app.schemas.audit import AuditLogResponse
from app.schemas.response import PaginatedResponse
from datetime import datetime

router = APIRouter(prefix="/audit", tags=["Audit Logs"])


@router.get(
    "/logs",
    response_model=PaginatedResponse[AuditLogResponse],
    summary="Query audit logs",
    description=(
        "Retrieve audit log entries with optional filtering by user, action, "
        "resource, and date range. Requires 'audit:list' permission."
    ),
    dependencies=[Depends(require_permissions(["audit:list"]))],
)
async def list_audit_logs(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    user_id: Optional[uuid.UUID] = Query(None, description="Filter by user ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    resource: Optional[str] = Query(None, description="Filter by resource"),
    start_date: Optional[datetime] = Query(None, description="Filter from date"),
    end_date: Optional[datetime] = Query(None, description="Filter to date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> PaginatedResponse[AuditLogResponse]:
    """Query audit logs with filters."""
    stmt = select(AuditLog)

    if user_id is not None:
        stmt = stmt.where(AuditLog.user_id == user_id)
    if action is not None:
        stmt = stmt.where(AuditLog.action == action)
    if resource is not None:
        stmt = stmt.where(AuditLog.resource == resource)
    if start_date is not None:
        stmt = stmt.where(AuditLog.created_at >= start_date)
    if end_date is not None:
        stmt = stmt.where(AuditLog.created_at <= end_date)

    # Get total count
    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await session.execute(count_stmt)
    total = total_result.scalar_one()

    # Get paginated results
    stmt = stmt.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    result = await session.execute(stmt)
    logs = result.scalars().all()

    log_responses = [
        AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            action=log.action,
            resource=log.resource,
            resource_id=log.resource_id,
            details=log.details,
            ip_address=log.ip_address,
            user_agent=log.user_agent,
            status_code=log.status_code,
            endpoint=log.endpoint,
            execution_time_ms=log.execution_time_ms,
            created_at=log.created_at,
        )
        for log in logs
    ]

    return PaginatedResponse(
        data=log_responses,
        total=total,
        skip=skip,
        limit=limit,
        message="Audit logs retrieved successfully",
    )
