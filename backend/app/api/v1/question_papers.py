"""
ExamShield - Question Paper Management API Routes

Endpoints for question paper upload, lifecycle management, and
version control with role-based access control and audit logging.
"""

import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile

from app.core.dependencies import (
    CurrentUser,
    get_question_paper_service,
    require_permissions,
)
from app.schemas.question_paper import (
    QuestionPaperResponse,
    QuestionPaperStatistics,
    QuestionPaperUpdate,
    QuestionPaperUpload,
    QuestionPaperVersionResponse,
)
from app.schemas.response import APIResponse, PaginatedResponse
from app.services.question_paper_service import QuestionPaperService

router = APIRouter(tags=["Question Paper Management"])


@router.post(
    "/question-papers/upload",
    response_model=APIResponse[QuestionPaperResponse],
    status_code=201,
    summary="Upload question paper",
    description="Upload a new question paper PDF. Requires 'questionpapers:create' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:create"]))],
)
async def upload_question_paper(
    request: Request,
    current_user: CurrentUser,
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
    subject_id: uuid.UUID = Form(...),
    paper_code: str = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
) -> APIResponse[QuestionPaperResponse]:
    """Upload a new question paper (creates new version if code exists)."""
    upload_data = QuestionPaperUpload(
        subject_id=subject_id,
        paper_code=paper_code,
        title=title,
        description=description,
    )
    
    paper = await service.upload_paper(
        upload_data=upload_data,
        file=file,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=paper, message="Question paper uploaded successfully")


@router.get(
    "/question-papers",
    response_model=PaginatedResponse[QuestionPaperResponse],
    summary="List all question papers",
    description="Retrieve a paginated list of question papers with optional filters. "
    "Requires 'questionpapers:read' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:read"]))],
)
async def list_question_papers(
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search by code or title"),
    subject_id: Optional[uuid.UUID] = Query(None, description="Filter by subject ID"),
) -> PaginatedResponse[QuestionPaperResponse]:
    """List question papers with optional filters."""
    papers = await service.list_papers(
        skip=skip,
        limit=limit,
        status=status,
        search=search,
        subject_id=subject_id,
    )
    total = await service.count_papers(
        status=status,
        search=search,
        subject_id=subject_id,
    )
    return PaginatedResponse(
        data=papers,
        total=total,
        skip=skip,
        limit=limit,
        message="Question papers retrieved successfully",
    )


@router.get(
    "/question-papers/statistics",
    response_model=APIResponse[QuestionPaperStatistics],
    summary="Get question paper statistics",
    description="Retrieve question paper counts grouped by status. "
    "Requires 'questionpapers:read' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:read"]))],
)
async def get_statistics(
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
) -> APIResponse[QuestionPaperStatistics]:
    """Get question paper dashboard statistics."""
    stats = await service.get_statistics()
    return APIResponse.ok(data=stats, message="Statistics retrieved successfully")


@router.get(
    "/question-papers/{paper_id}",
    response_model=APIResponse[QuestionPaperResponse],
    summary="Get question paper by ID",
    description="Retrieve a specific question paper by its UUID. "
    "Requires 'questionpapers:read' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:read"]))],
)
async def get_question_paper(
    paper_id: uuid.UUID,
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
) -> APIResponse[QuestionPaperResponse]:
    """Get a single question paper by ID."""
    paper = await service.get_paper(paper_id)
    return APIResponse.ok(data=paper, message="Question paper retrieved successfully")


@router.get(
    "/question-papers/{paper_id}/versions",
    response_model=APIResponse[list[QuestionPaperVersionResponse]],
    summary="Get question paper versions",
    description="Retrieve all versions of a specific question paper. "
    "Requires 'questionpapers:read' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:read"]))],
)
async def get_question_paper_versions(
    paper_id: uuid.UUID,
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
) -> APIResponse[list[QuestionPaperVersionResponse]]:
    """Get all versions of a question paper."""
    versions = await service.get_versions(paper_id)
    return APIResponse.ok(data=versions, message="Versions retrieved successfully")


@router.put(
    "/question-papers/{paper_id}",
    response_model=APIResponse[QuestionPaperResponse],
    summary="Update question paper",
    description="Update a question paper's metadata or transition its status. "
    "Requires 'questionpapers:update' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:update"]))],
)
async def update_question_paper(
    paper_id: uuid.UUID,
    update_data: QuestionPaperUpdate,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
) -> APIResponse[QuestionPaperResponse]:
    """Update a question paper."""
    paper = await service.update_paper(
        paper_id=paper_id,
        update_data=update_data,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=paper, message="Question paper updated successfully")


@router.delete(
    "/question-papers/{paper_id}",
    response_model=APIResponse[None],
    summary="Delete question paper",
    description="Delete a question paper. Approved or archived papers cannot be deleted. "
    "Requires 'questionpapers:delete' permission.",
    dependencies=[Depends(require_permissions(["questionpapers:delete"]))],
)
async def delete_question_paper(
    paper_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[QuestionPaperService, Depends(get_question_paper_service)],
) -> APIResponse[None]:
    """Delete a question paper."""
    await service.delete_paper(
        paper_id=paper_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(message="Question paper deleted successfully")
