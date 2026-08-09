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

    async def generate_key_metadata(
        self, algorithm: Algorithm, purpose: KeyPurpose, created_by: str
    ) -> KeyMetadata:
        now = datetime.now(timezone.utc)
        return KeyMetadata(
            key_identifier=f"localkms-{uuid.uuid4()}",
            algorithm=algorithm,
            key_purpose=purpose,
            key_version=1,
            status=KeyStatus.INACTIVE,
            rotation_due=now + timedelta(days=90),
            created_by=uuid.UUID(created_by) if created_by else None,
        )

    async def rotate_key(self, current_key_identifier: str) -> KeyMetadata:
        now = datetime.now(timezone.utc)
        # Mock logic: returns a new metadata instance with version 2
        return KeyMetadata(
            key_identifier=f"localkms-{uuid.uuid4()}",
            algorithm=Algorithm.AES256_GCM,
            key_purpose=KeyPurpose.ENCRYPTION,
            key_version=2,
            status=KeyStatus.INACTIVE,
            rotation_due=now + timedelta(days=90),
        )

    async def activate_key(self, key_identifier: str) -> bool:
        return True

    async def deactivate_key(self, key_identifier: str) -> bool:
        return True

    async def list_active_keys(self) -> List[KeyMetadata]:
        return []

    async def get_key_metadata(self, key_identifier: str) -> KeyMetadata:
        now = datetime.now(timezone.utc)
        return KeyMetadata(
            key_identifier=key_identifier,
            algorithm=Algorithm.AES256_GCM,
            key_purpose=KeyPurpose.ENCRYPTION,
            key_version=1,
            status=KeyStatus.ACTIVE,
            activated_at=now,
        )
