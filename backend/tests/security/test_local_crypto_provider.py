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


@pytest.mark.asyncio
async def test_key_persistence_across_restarts(tmp_path):
    """Verify that a generated RSA wrapping key survives a process restart/redeployment when the volume is mounted."""
    key_dir = tmp_path / "persistent_local_keys"
    provider1 = LocalCryptoKeyProvider(key_dir=key_dir)
    key_identifier = "staging-rsa-key-persist"

    await provider1.generate_rsa_key(key_identifier)
    session_key = b"0123456789abcdef0123456789abcdef"
    wrapped = await provider1.wrap_key(key_identifier, session_key)

    # Simulate process restart by instantiating a new provider pointing to the same mounted key directory
    provider2 = LocalCryptoKeyProvider(key_dir=key_dir)
    assert await provider2.validate_key_availability(key_identifier) is True

    unwrapped = await provider2.unwrap_key(key_identifier, wrapped)
    assert unwrapped == session_key


@pytest.mark.asyncio
async def test_local_crypto_provider_custom_dir(tmp_path):
    """Verify LocalCryptoKeyProvider initializes cleanly at custom key_dir (e.g. /app/data/.local_keys)."""
    custom_dir = tmp_path / "app" / "data" / ".local_keys"
    provider = LocalCryptoKeyProvider(key_dir=custom_dir)
    assert provider._key_dir == custom_dir.resolve()
    assert custom_dir.exists()


@pytest.mark.asyncio
async def test_local_crypto_provider_env_dir(tmp_path, monkeypatch):
    """Verify LocalCryptoKeyProvider uses LOCAL_KEYS_DIR environment variable when key_dir is not provided."""
    env_dir = tmp_path / "app" / "data" / ".local_keys_env"
    monkeypatch.setenv("LOCAL_KEYS_DIR", str(env_dir))
    provider = LocalCryptoKeyProvider()
    assert provider._key_dir == env_dir.resolve()
    assert env_dir.exists()