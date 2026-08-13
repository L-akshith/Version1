import uuid

import pytest

from app.models.key_metadata import (
    Algorithm,
    KeyPurpose,
)
from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)
from app.modules.security.providers.local_provider import (
    LocalKeyProvider,
)


@pytest.mark.asyncio
async def test_rsa_key_can_be_registered_and_used():

    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    user_id = uuid.uuid4()

    metadata = await metadata_provider.generate_key_metadata(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        created_by=str(user_id),
    )

    await crypto_provider.generate_rsa_key(
        metadata.key_identifier
    )

    aes_key = b"0123456789abcdef0123456789abcdef"

    wrapped = await crypto_provider.wrap_key(
        metadata.key_identifier,
        aes_key,
    )

    unwrapped = await crypto_provider.unwrap_key(
        metadata.key_identifier,
        wrapped,
    )

    assert unwrapped == aes_key
    assert wrapped != aes_key