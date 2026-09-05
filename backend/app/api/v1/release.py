"""
ExamShield - Release API Endpoints
"""

import uuid
from typing import Dict, Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_crypto_key_provider, require_permissions
from app.schemas.release import ReleaseScheduleCreate, ReleaseScheduleResponse
from app.schemas.response import APIResponse, PaginatedResponse
from app.services.release_service import ReleaseService


router = APIRouter()

@router.post(
    "/{paper_id}/schedule",
    response_model=ReleaseScheduleResponse,
)
async def schedule_release(
    paper_id: uuid.UUID,
    data: ReleaseScheduleCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    crypto_provider = Depends(get_crypto_key_provider),
    user=Depends(require_permissions(["papers:release"])),
):
    service = ReleaseService(db, crypto_provider)
    return await service.schedule_release(
        paper_id=paper_id,
        data=data,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )

@router.post(
    "/{paper_id}/execute",
)
async def execute_release(
    paper_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    crypto_provider = Depends(get_crypto_key_provider),
    user=Depends(require_permissions(["papers:release"])),
):
    service = ReleaseService(db, crypto_provider)
    success = await service.execute_release(
        paper_id=paper_id,
        user_id=user.id,
        ip_address=request.client.host if request.client else None,
    )
    return {"status": "success" if success else "failed"}

@router.get(
    "/schedules/upcoming",
    response_model=PaginatedResponse[ReleaseScheduleResponse],
)
async def list_upcoming_schedules(
    skip: int = 0,
    limit: int = 100,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    crypto_provider = Depends(get_crypto_key_provider),
    user=Depends(require_permissions(["papers:release"])),
):
    service = ReleaseService(db, crypto_provider)
    schedules = await service.list_schedules(
        skip=skip,
        limit=limit,
        status=status,
    )
    return PaginatedResponse(
        data=schedules,
        total=len(schedules),
        skip=skip,
        limit=limit,
        message="Upcoming schedules retrieved successfully",
    )

