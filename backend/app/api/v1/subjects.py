"""
ExamShield - Subject Management API Routes

CRUD endpoints for subject lifecycle management with
role-based access control and audit logging.
"""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, Request

from app.core.dependencies import (
    CurrentUser,
    get_subject_service,
    require_permissions,
)
from app.schemas.response import APIResponse, PaginatedResponse
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectStatistics,
    SubjectUpdate,
)
from app.services.subject_service import SubjectService

router = APIRouter(tags=["Subject Management"])

# We define the endpoints under /subjects and /exams/{exam_id}/subjects
# The main app.include_router will mount this without prefix to handle both paths


@router.post(
    "/subjects",
    response_model=APIResponse[SubjectResponse],
    status_code=201,
    summary="Create a new subject",
    description="Create a new subject within an exam. Requires 'subjects:create' permission.",
    dependencies=[Depends(require_permissions(["subjects:create"]))],
)
async def create_subject(
    request_body: SubjectCreate,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[SubjectService, Depends(get_subject_service)],
) -> APIResponse[SubjectResponse]:
    """Create a new subject."""
    subject = await service.create_subject(
        request=request_body,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=subject, message="Subject created successfully")


@router.get(
    "/subjects",
    response_model=PaginatedResponse[SubjectResponse],
    summary="List all subjects",
    description="Retrieve a paginated list of subjects with optional filters. "
    "Requires 'subjects:read' permission.",
    dependencies=[Depends(require_permissions(["subjects:read"]))],
)
async def list_subjects(
    service: Annotated[SubjectService, Depends(get_subject_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by code or name"),
    exam_id: Optional[uuid.UUID] = Query(None, description="Filter by exam ID"),
) -> PaginatedResponse[SubjectResponse]:
    """List subjects with optional filters."""
    subjects = await service.list_subjects(
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        exam_id=exam_id,
    )
    total = await service.count_subjects(
        status=status,
        search=search,
        exam_id=exam_id,
    )
    return PaginatedResponse(
        data=subjects,
        total=total,
        skip=skip,
        limit=limit,
        message="Subjects retrieved successfully",
    )


@router.get(
    "/subjects/statistics",
    response_model=APIResponse[SubjectStatistics],
    summary="Get subject statistics",
    description="Retrieve subject counts grouped by status. "
    "Requires 'subjects:read' permission.",
    dependencies=[Depends(require_permissions(["subjects:read"]))],
)
async def get_statistics(
    service: Annotated[SubjectService, Depends(get_subject_service)],
) -> APIResponse[SubjectStatistics]:
    """Get subject dashboard statistics."""
    stats = await service.get_statistics()
    return APIResponse.ok(data=stats, message="Statistics retrieved successfully")


@router.get(
    "/subjects/{subject_id}",
    response_model=APIResponse[SubjectResponse],
    summary="Get subject by ID",
    description="Retrieve a specific subject by its UUID. "
    "Requires 'subjects:read' permission.",
    dependencies=[Depends(require_permissions(["subjects:read"]))],
)
async def get_subject(
    subject_id: uuid.UUID,
    service: Annotated[SubjectService, Depends(get_subject_service)],
) -> APIResponse[SubjectResponse]:
    """Get a single subject by ID."""
    subject = await service.get_subject(subject_id)
    return APIResponse.ok(data=subject, message="Subject retrieved successfully")


@router.get(
    "/exams/{exam_id}/subjects",
    response_model=PaginatedResponse[SubjectResponse],
    summary="List subjects for an exam",
    description="Retrieve all subjects belonging to a specific exam. "
    "Requires 'subjects:read' permission.",
    dependencies=[Depends(require_permissions(["subjects:read"]))],
)
async def list_subjects_by_exam(
    exam_id: uuid.UUID,
    service: Annotated[SubjectService, Depends(get_subject_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
) -> PaginatedResponse[SubjectResponse]:
    """List subjects for a specific exam."""
    subjects = await service.list_by_exam(
        exam_id=exam_id,
        skip=skip,
        limit=limit,
    )
    total = await service.count_subjects(exam_id=exam_id)
    return PaginatedResponse(
        data=subjects,
        total=total,
        skip=skip,
        limit=limit,
        message="Subjects retrieved successfully",
    )


@router.put(
    "/subjects/{subject_id}",
    response_model=APIResponse[SubjectResponse],
    summary="Update subject",
    description="Update a subject's details or transition its status. "
    "Requires 'subjects:update' permission.",
    dependencies=[Depends(require_permissions(["subjects:update"]))],
)
async def update_subject(
    subject_id: uuid.UUID,
    update_data: SubjectUpdate,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[SubjectService, Depends(get_subject_service)],
) -> APIResponse[SubjectResponse]:
    """Update a subject."""
    subject = await service.update_subject(
        subject_id=subject_id,
        update_data=update_data,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=subject, message="Subject updated successfully")


@router.delete(
    "/subjects/{subject_id}",
    response_model=APIResponse[None],
    summary="Delete subject",
    description="Delete a subject. Archived subjects cannot be deleted. "
    "Requires 'subjects:delete' permission.",
    dependencies=[Depends(require_permissions(["subjects:delete"]))],
)
async def delete_subject(
    subject_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[SubjectService, Depends(get_subject_service)],
) -> APIResponse[None]:
    """Delete a subject."""
    await service.delete_subject(
        subject_id=subject_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(message="Subject deleted successfully")
