"""
ExamShield - Local Development Key Provider

Mock provider that satisfies the KeyProvider interface without actual cryptographic ops.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List

from app.models.key_metadata import Algorithm, KeyMetadata, KeyPurpose, KeyStatus
from app.modules.security.interfaces.key_provider import KeyProvider


class LocalKeyProvider(KeyProvider):
    """
    Mock KMS for local development. Generates metadata but does not securely 
    store or utilize real cryptographic keys.
    """

    def __init__(self):
        self._keys: dict[str, KeyMetadata] = {}

    async def generate_key_metadata(
        self, algorithm: Algorithm, purpose: KeyPurpose, created_by: str
    ) -> KeyMetadata:
        now = datetime.now(timezone.utc)
        metadata = KeyMetadata(
            key_identifier=f"localkms-{uuid.uuid4()}",
            algorithm=algorithm,
            key_purpose=purpose,
            key_version=1,
            status=KeyStatus.INACTIVE,
            rotation_due=now + timedelta(days=90),
            created_by=uuid.UUID(created_by) if created_by else None,
        )
        self._keys[metadata.key_identifier] = metadata
        return metadata

    async def rotate_key(
        self,
        current_key_identifier: str,
    ) -> KeyMetadata:

        current_key = await self.get_key_metadata(
            current_key_identifier
        )

        now = datetime.now(timezone.utc)

        new_metadata = KeyMetadata(
            key_identifier=f"localkms-{uuid.uuid4()}",
            algorithm=current_key.algorithm,
            key_purpose=current_key.key_purpose,
            key_version=current_key.key_version + 1,
            status=KeyStatus.INACTIVE,
            rotation_due=now + timedelta(days=90),
        )
        self._keys[new_metadata.key_identifier] = new_metadata
        return new_metadata

    async def activate_key(self, key_identifier: str) -> bool:
        if key_identifier in self._keys:
            self._keys[key_identifier].status = KeyStatus.ACTIVE
            self._keys[key_identifier].activated_at = datetime.now(timezone.utc)
        return True

    async def deactivate_key(self, key_identifier: str) -> bool:
        if key_identifier in self._keys:
            self._keys[key_identifier].status = KeyStatus.INACTIVE
            self._keys[key_identifier].deactivated_at = datetime.now(timezone.utc)
        return True

    async def list_active_keys(self) -> List[KeyMetadata]:
        return [k for k in self._keys.values() if k.status == KeyStatus.ACTIVE]

    async def get_key_metadata(self, key_identifier: str) -> KeyMetadata:
        if key_identifier in self._keys:
            return self._keys[key_identifier]
        now = datetime.now(timezone.utc)
        return KeyMetadata(
            key_identifier=key_identifier,
            algorithm=Algorithm.AES256_GCM,
            key_purpose=KeyPurpose.ENCRYPTION,
            key_version=1,
            status=KeyStatus.ACTIVE,
            activated_at=now,
        )
