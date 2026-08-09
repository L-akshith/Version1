"""
ExamShield - Key Management Service

Business logic for cryptographic key lifecycle, ensuring keys are safely generated,
rotated, activated, and revoked without ever exposing raw key materials.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import BadRequestException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.key_metadata import Algorithm, KeyMetadata, KeyPurpose, KeyStatus
from app.modules.security.interfaces.key_provider import KeyProvider
from app.modules.security.repositories.key_repository import KeyMetadataRepository


class KeyManagementService:
    """Service to handle business operations related to key lifecycle."""

    def __init__(self, session: AsyncSession, provider: KeyProvider) -> None:
        self._session = session
        self._repo = KeyMetadataRepository(session)
        self._provider = provider

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None,
    ) -> None:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="keys",
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    async def list_keys(self) -> List[KeyMetadata]:
        return await self._repo.get_all_keys()

    async def get_key(self, key_id: uuid.UUID) -> KeyMetadata:
        key = await self._repo.get_by_id(key_id)
        if not key:
            raise NotFoundException(f"Key metadata '{key_id}' not found.")
        return key

    async def generate_key(
        self, algorithm: Algorithm, purpose: KeyPurpose, user_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> KeyMetadata:
        """Request the KMS to generate a new key and save its metadata."""
        metadata = await self._provider.generate_key_metadata(
            algorithm=algorithm, purpose=purpose, created_by=str(user_id)
        )
        self._session.add(metadata)
        await self._session.flush()

        await self._create_audit_entry(
            user_id=user_id,
            action="key_generate",
            resource_id=str(metadata.id),
            details={"algorithm": algorithm.value, "purpose": purpose.value},
            ip_address=ip_address,
        )
        return metadata

    async def activate_key(
        self, key_id: uuid.UUID, user_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> KeyMetadata:
        """Activate an inactive key."""
        key = await self.get_key(key_id)
        if key.status != KeyStatus.INACTIVE:
            raise BadRequestException(f"Key is currently {key.status}, cannot activate.")

        # Activate on provider
        success = await self._provider.activate_key(key.key_identifier)
        if not success:
            raise BadRequestException("KMS failed to activate key.")

        key.status = KeyStatus.ACTIVE
        key.activated_at = datetime.now(timezone.utc)
        await self._session.flush()

        await self._create_audit_entry(
            user_id=user_id,
            action="key_activate",
            resource_id=str(key.id),
            details={"key_identifier": key.key_identifier},
            ip_address=ip_address,
        )
        return key

    async def deactivate_key(
        self, key_id: uuid.UUID, user_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> KeyMetadata:
        """Deactivate a currently active key."""
        key = await self.get_key(key_id)
        if key.status != KeyStatus.ACTIVE:
            raise BadRequestException(f"Key is currently {key.status}, cannot deactivate.")

        # Deactivate on provider
        success = await self._provider.deactivate_key(key.key_identifier)
        if not success:
            raise BadRequestException("KMS failed to deactivate key.")

        key.status = KeyStatus.INACTIVE
        key.deactivated_at = datetime.now(timezone.utc)
        await self._session.flush()

        await self._create_audit_entry(
            user_id=user_id,
            action="key_deactivate",
            resource_id=str(key.id),
            details={"key_identifier": key.key_identifier},
            ip_address=ip_address,
        )
        return key

    async def rotate_key(
        self, key_id: uuid.UUID, user_id: uuid.UUID, ip_address: Optional[str] = None
    ) -> KeyMetadata:
        """Rotate a key to a new version."""
        old_key = await self.get_key(key_id)
        
        # Generate new version via provider
        new_key_metadata = await self._provider.rotate_key(old_key.key_identifier)
        new_key_metadata.created_by = user_id
        self._session.add(new_key_metadata)
        
        # Deactivate old key locally
        if old_key.status == KeyStatus.ACTIVE:
            old_key.status = KeyStatus.INACTIVE
            old_key.deactivated_at = datetime.now(timezone.utc)

        await self._session.flush()

        await self._create_audit_entry(
            user_id=user_id,
            action="key_rotate",
            resource_id=str(new_key_metadata.id),
            details={"rotated_from": str(old_key.id), "new_version": new_key_metadata.key_version},
            ip_address=ip_address,
        )
        return new_key_metadata
