import uuid

import pytest

from app.models.key_metadata import Algorithm, KeyPurpose
from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)
from app.modules.security.providers.local_provider import (
    LocalKeyProvider,
)
from app.modules.security.services.key_management_service import (
    KeyManagementService,
)


@pytest.mark.asyncio
async def test_rsa_key_rotation_preserves_algorithm_and_purpose(
    db_session,
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    user_id = uuid.uuid4()

    original = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=user_id,
    )

    rotated = await service.rotate_key(
        key_id=original.id,
        user_id=user_id,
    )

    assert rotated.algorithm == Algorithm.RSA4096
    assert rotated.key_purpose == KeyPurpose.WRAPPING
    assert rotated.key_version == original.key_version + 1
    assert rotated.key_identifier != original.key_identifier


@pytest.mark.asyncio
async def test_rotated_rsa_key_is_usable(
    db_session,
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    original = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=uuid.uuid4(),
    )

    rotated = await service.rotate_key(
        key_id=original.id,
        user_id=uuid.uuid4(),
    )

    aes_key = b"0123456789abcdef0123456789abcdef"

    wrapped = await crypto_provider.wrap_key(
        rotated.key_identifier,
        aes_key,
    )

    unwrapped = await crypto_provider.unwrap_key(
        rotated.key_identifier,
        wrapped,
    )

    # assert unwrapped == aes_key See I don't know Hey Cortana What is it Professional teacher was a teacher