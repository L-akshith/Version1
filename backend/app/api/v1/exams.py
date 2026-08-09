"""
ExamShield - Exam Management API Routes

CRUD endpoints for examination lifecycle management with
role-based access control and audit logging.
"""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import (
    CurrentUser,
    require_permissions,
    get_async_session,
)
from app.database.session import get_async_session
from app.schemas.exam import ExamCreate, ExamResponse, ExamStatistics, ExamUpdate
from app.schemas.response import APIResponse, PaginatedResponse
from app.services.exam_service import ExamService

router = APIRouter(prefix="/exams", tags=["Exam Management"])


@router.post(
    "",
    response_model=APIResponse[ExamResponse],
    status_code=201,
    summary="Create a new examination",
    description="Create a new exam entry in the system. Requires 'exams:create' permission.",
    dependencies=[Depends(require_permissions(["exams:create"]))],
)
async def create_exam(
    request_body: ExamCreate,
    request: Request,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[ExamResponse]:
    """Create a new examination."""
    service = ExamService(session)
    exam = await service.create_exam(
        request=request_body,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=exam, message="Examination created successfully")


@router.get(
    "",
    response_model=PaginatedResponse[ExamResponse],
    summary="List all examinations",
    description="Retrieve a paginated list of examinations with optional filters. "
    "Requires 'exams:read' permission.",
    dependencies=[Depends(require_permissions(["exams:read"]))],
)
async def list_exams(
    session: Annotated[AsyncSession, Depends(get_async_session)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by exam code or name"),
    year: Optional[int] = Query(None, ge=2000, le=2100, description="Filter by year"),
) -> PaginatedResponse[ExamResponse]:
    """List examinations with optional filters."""
    service = ExamService(session)
    exams = await service.list_exams(
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        year=year,
    )
    total = await service.count_exams(
        status=status,
        search=search,
        year=year,
    )
    return PaginatedResponse(
        data=exams,
        total=total,
        skip=skip,
        limit=limit,
        message="Examinations retrieved successfully",
    )


@router.get(
    "/statistics",
    response_model=APIResponse[ExamStatistics],
    summary="Get exam statistics",
    description="Retrieve examination counts grouped by status. "
    "Requires 'exams:read' permission.",
    dependencies=[Depends(require_permissions(["exams:read"]))],
)
async def get_statistics(
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[ExamStatistics]:
    """Get exam dashboard statistics."""
    service = ExamService(session)
    stats = await service.get_statistics()
    return APIResponse.ok(data=stats, message="Statistics retrieved successfully")


@router.get(
    "/{exam_id}",
    response_model=APIResponse[ExamResponse],
    summary="Get exam by ID",
    description="Retrieve a specific examination by its UUID. "
    "Requires 'exams:read' permission.",
    dependencies=[Depends(require_permissions(["exams:read"]))],
)
async def get_exam(
    exam_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[ExamResponse]:
    """Get a single examination by ID."""
    service = ExamService(session)
    exam = await service.get_exam(exam_id)
    return APIResponse.ok(data=exam, message="Examination retrieved successfully")


@router.put(
    "/{exam_id}",
    response_model=APIResponse[ExamResponse],
    summary="Update examination",
    description="Update an examination's details or transition its status. "
    "Requires 'exams:update' permission.",
    dependencies=[Depends(require_permissions(["exams:update"]))],
)
async def update_exam(
    exam_id: uuid.UUID,
    update_data: ExamUpdate,
    request: Request,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[ExamResponse]:
    """Update an examination."""
    service = ExamService(session)
    exam = await service.update_exam(
        exam_id=exam_id,
        update_data=update_data,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=exam, message="Examination updated successfully")


@router.delete(
    "/{exam_id}",
    response_model=APIResponse[None],
    summary="Delete examination",
    description="Delete an examination. Active exams cannot be deleted. "
    "Requires 'exams:delete' permission.",
    dependencies=[Depends(require_permissions(["exams:delete"]))],
)
async def delete_exam(
    exam_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    session: Annotated[AsyncSession, Depends(get_async_session)],
) -> APIResponse[None]:
    """Delete an examination."""
    service = ExamService(session)
    await service.delete_exam(
        exam_id=exam_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(message="Examination deleted successfully")
