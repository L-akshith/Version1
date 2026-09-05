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

@pytest.mark.asyncio
async def test_crypto_provider_persistence():
    provider = LocalCryptoKeyProvider()
    key_identifier = f"localkms-{uuid.uuid4()}"
    await provider.generate_rsa_key(key_identifier)

    assert await provider.validate_key_availability(key_identifier)

    # Clear memory cache
    del provider._private_keys[key_identifier]
    
    assert await provider.validate_key_availability(key_identifier)

    # Should still be able to use it
    aes_key = b"0123456789abcdef0123456789abcdef"
    wrapped = await provider.wrap_key(key_identifier, aes_key)
    unwrapped = await provider.unwrap_key(key_identifier, wrapped)
    assert unwrapped == aes_key

@pytest.mark.asyncio
async def test_unwrap_missing_key_raises_key_error():
    provider = LocalCryptoKeyProvider()
    key_identifier = "nonexistent-key"
    
    assert not await provider.validate_key_availability(key_identifier)

    with pytest.raises(KeyError, match="not found"):
        await provider.unwrap_key(key_identifier, b"fake_wrapped")