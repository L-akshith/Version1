"""
ExamShield - Center Management Service

Business logic for registering and managing examination centers,
including key provisioning and revocations.
"""

import uuid
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import BadRequestException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.examination_center import CenterStatus
from app.repositories.examination_center_repository import ExaminationCenterRepository
from app.schemas.examination_center import (
    ExaminationCenterCreate,
    ExaminationCenterResponse,
    KeyProvisionRequest,
)


class CenterManagementService:
    """Service layer for examination center operations."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._center_repo = ExaminationCenterRepository(session)

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry."""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="examination_centers",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    async def register_center(
        self,
        data: ExaminationCenterCreate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ExaminationCenterResponse:
        """Register a new examination center."""
        existing = await self._center_repo.get_by_code(data.center_code)
        if existing:
            raise BadRequestException(message=f"Center code '{data.center_code}' already exists")

        center = await self._center_repo.create({
            "center_code": data.center_code,
            "name": data.name,
            "status": CenterStatus.ACTIVE,
        })

        await self._create_audit_entry(
            user_id=user_id,
            action="center_registered",
            resource_id=str(center.id),
            details={"center_code": center.center_code},
            ip_address=ip_address,
        )

        return ExaminationCenterResponse.model_validate(center)

    async def provision_key(
        self,
        center_id: uuid.UUID,
        data: KeyProvisionRequest,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ExaminationCenterResponse:
        """
        Provision or rotate the RSA public key for an examination center.
        """
        center = await self._center_repo.get_by_id(center_id)
        if not center:
            raise NotFoundException(message=f"Center with ID '{center_id}' not found")
            
        if center.status == CenterStatus.REVOKED:
            raise BadRequestException(message="Cannot provision key for a revoked center")

        # In a real scenario, we might want to validate that the PEM string is actually
        # a valid RSA public key format before saving it.
        # For now, we trust the input per the design.

        await self._center_repo.update(center_id, {
            "public_key_pem": data.public_key_pem,
            "key_identifier": data.key_identifier,
        })
        
        updated_center = await self._center_repo.get_by_id(center_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="center_key_provisioned",
            resource_id=str(center_id),
            details={"key_identifier": data.key_identifier},
            ip_address=ip_address,
        )

        return ExaminationCenterResponse.model_validate(updated_center)

    async def revoke_center(
        self,
        center_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ExaminationCenterResponse:
        """Revoke a center, preventing it from receiving new releases."""
        center = await self._center_repo.get_by_id(center_id)
        if not center:
            raise NotFoundException(message=f"Center with ID '{center_id}' not found")

        await self._center_repo.update(center_id, {"status": CenterStatus.REVOKED})
        updated_center = await self._center_repo.get_by_id(center_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="center_revoked",
            resource_id=str(center_id),
            details={"center_code": center.center_code},
            ip_address=ip_address,
        )

        return ExaminationCenterResponse.model_validate(updated_center)

    async def list_centers(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ExaminationCenterResponse]:
        """List examination centers."""
        centers = await self._center_repo.list_centers(
            skip=skip, limit=limit, status=status, search=search
        )
        return [ExaminationCenterResponse.model_validate(c) for c in centers]
