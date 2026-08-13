import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.key_metadata import Algorithm, KeyPurpose, KeyStatus
from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)
from app.modules.security.providers.local_provider import LocalKeyProvider
from app.modules.security.services.key_management_service import (
    KeyManagementService,
)


@pytest.mark.asyncio
async def test_generate_rsa_key_creates_metadata_and_crypto_key(
    db_session: AsyncSession,
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    user_id = uuid.uuid4()

    metadata = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=user_id,
    )

    assert metadata is not None
    assert metadata.key_identifier.startswith("localkms-")
    assert metadata.algorithm == Algorithm.RSA4096
    assert metadata.key_purpose == KeyPurpose.WRAPPING

    public_key = await crypto_provider.get_public_key(
        metadata.key_identifier
    )

    assert public_key is not None
    assert public_key.key_size == 4096


@pytest.mark.asyncio
async def test_generated_rsa_key_can_wrap_and_unwrap_aes_key(
    db_session: AsyncSession,
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    metadata = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=uuid.uuid4(),
    )

    aes_key = b"0123456789abcdef0123456789abcdef"

    wrapped_key = await crypto_provider.wrap_key(
        metadata.key_identifier,
        aes_key,
    )

    unwrapped_key = await crypto_provider.unwrap_key(
        metadata.key_identifier,
        wrapped_key,
    )

    assert unwrapped_key == aes_key
    assert wrapped_key != aes_key