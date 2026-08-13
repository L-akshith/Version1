import pytest

from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)


@pytest.mark.asyncio
async def test_wrap_and_unwrap_key():

    provider = LocalCryptoKeyProvider()

    key_identifier = "test-rsa-key"

    await provider.generate_rsa_key(key_identifier)

    original_key = b"0123456789abcdef0123456789abcdef"

    wrapped_key = await provider.wrap_key(
        key_identifier,
        original_key,
    )

    unwrapped_key = await provider.unwrap_key(
        key_identifier,
        wrapped_key,
    )

    assert wrapped_key != original_key
    assert unwrapped_key == original_key


@pytest.mark.asyncio
async def test_unknown_key_fails():

    provider = LocalCryptoKeyProvider()

    with pytest.raises(KeyError):

        await provider.get_public_key(
            "does-not-exist"
        )


@pytest.mark.asyncio
async def test_wrong_key_identifier_fails():

    provider = LocalCryptoKeyProvider()

    await provider.generate_rsa_key("key-1")
    await provider.generate_rsa_key("key-2")

    original_key = b"0123456789abcdef0123456789abcdef"

    wrapped_key = await provider.wrap_key(
        "key-1",
        original_key,
    )

    with pytest.raises(Exception):

        await provider.unwrap_key(
            "key-2",
            wrapped_key,
        )