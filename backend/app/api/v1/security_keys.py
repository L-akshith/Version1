"""
ExamShield - Security Keys API Routes

Endpoints for cryptographic key lifecycle management.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app.core.dependencies import CurrentUser, get_key_management_service, require_permissions
from app.modules.security.schemas.key_schemas import GenerateKeyRequest, KeyMetadataResponse
from app.modules.security.services.key_management_service import KeyManagementService
from app.schemas.response import APIResponse

router = APIRouter(tags=["Security Keys"])


@router.get(
    "/security/keys",
    response_model=APIResponse[list[KeyMetadataResponse]],
    summary="List keys",
    dependencies=[Depends(require_permissions(["keys:read"]))],
)
async def list_keys(
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[list[KeyMetadataResponse]]:
    """List all cryptographic keys metadata."""
    keys = await service.list_keys()
    return APIResponse.ok(data=keys)


@router.get(
    "/security/keys/{key_id}",
    response_model=APIResponse[KeyMetadataResponse],
    summary="Get key metadata",
    dependencies=[Depends(require_permissions(["keys:read"]))],
)
async def get_key(
    key_id: uuid.UUID,
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[KeyMetadataResponse]:
    """Get metadata for a specific key."""
    key = await service.get_key(key_id)
    return APIResponse.ok(data=key)


@router.post(
    "/security/keys",
    response_model=APIResponse[KeyMetadataResponse],
    summary="Generate key",
    dependencies=[Depends(require_permissions(["keys:create"]))],
)
async def generate_key(
    request: Request,
    current_user: CurrentUser,
    req_body: GenerateKeyRequest,
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[KeyMetadataResponse]:
    """Request generation of a new cryptographic key."""
    key = await service.generate_key(
        algorithm=req_body.algorithm,
        purpose=req_body.key_purpose,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=key, message="Key generated successfully")


@router.post(
    "/security/keys/{key_id}/activate",
    response_model=APIResponse[KeyMetadataResponse],
    summary="Activate key",
    dependencies=[Depends(require_permissions(["keys:manage"]))],
)
async def activate_key(
    key_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[KeyMetadataResponse]:
    """Activate an inactive key."""
    key = await service.activate_key(
        key_id=key_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=key, message="Key activated successfully")


@router.post(
    "/security/keys/{key_id}/deactivate",
    response_model=APIResponse[KeyMetadataResponse],
    summary="Deactivate key",
    dependencies=[Depends(require_permissions(["keys:manage"]))],
)
async def deactivate_key(
    key_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[KeyMetadataResponse]:
    """Deactivate an active key."""
    key = await service.deactivate_key(
        key_id=key_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=key, message="Key deactivated successfully")


@router.post(
    "/security/keys/{key_id}/rotate",
    response_model=APIResponse[KeyMetadataResponse],
    summary="Rotate key",
    dependencies=[Depends(require_permissions(["keys:manage"]))],
)
async def rotate_key(
    key_id: uuid.UUID,
    request: Request,
    current_user: CurrentUser,
    service: Annotated[KeyManagementService, Depends(get_key_management_service)],
) -> APIResponse[KeyMetadataResponse]:
    """Rotate an existing key."""
    key = await service.rotate_key(
        key_id=key_id,
        user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
    )
    return APIResponse.ok(data=key, message="Key rotated successfully")
