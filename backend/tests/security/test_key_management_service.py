import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.key_metadata import Algorithm, KeyPurpose, KeyStatus
from app.models.user import User
from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)
from app.modules.security.providers.local_provider import LocalKeyProvider
from app.modules.security.services.key_management_service import (
    KeyManagementService,
)


@pytest.mark.asyncio
async def test_generate_rsa_key_creates_metadata_and_crypto_key(
    db_session: AsyncSession, test_admin: User
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    user_id = test_admin.id

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
    db_session: AsyncSession, test_admin: User
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
        user_id=test_admin.id,
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

@pytest.mark.asyncio
async def test_generate_rsa_key_fails_transaction(
    db_session: AsyncSession, test_admin: User
):
    metadata_provider = LocalKeyProvider()
    class FailingCryptoProvider(LocalCryptoKeyProvider):
        async def generate_rsa_key(self, key_identifier: str) -> None:
            raise ValueError("Simulated crypto failure")

    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=FailingCryptoProvider(),
    )

    with pytest.raises(Exception, match="Failed to generate RSA key"):
        await service.generate_key(
            algorithm=Algorithm.RSA4096,
            purpose=KeyPurpose.WRAPPING,
            user_id=test_admin.id,
        )

@pytest.mark.asyncio
async def test_rotate_rsa_key(
    db_session: AsyncSession, test_admin: User
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()
    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    old_key = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=test_admin.id,
    )
    assert await crypto_provider.validate_key_availability(old_key.key_identifier)

    new_key = await service.rotate_key(
        key_id=old_key.id,
        user_id=test_admin.id,
    )

    assert new_key.key_identifier != old_key.key_identifier
    assert await crypto_provider.validate_key_availability(new_key.key_identifier)
    assert await crypto_provider.validate_key_availability(old_key.key_identifier)

@pytest.mark.asyncio
async def test_activate_missing_rsa_key_fails(
    db_session: AsyncSession, test_admin: User
):
    metadata_provider = LocalKeyProvider()
    crypto_provider = LocalCryptoKeyProvider()
    service = KeyManagementService(
        session=db_session,
        provider=metadata_provider,
        crypto_provider=crypto_provider,
    )

    key_metadata = await service.generate_key(
        algorithm=Algorithm.RSA4096,
        purpose=KeyPurpose.WRAPPING,
        user_id=test_admin.id,
    )

    # Delete the PEM file to simulate missing key
    pem_path = crypto_provider._pem_path(key_metadata.key_identifier)
    if pem_path.exists():
        pem_path.unlink()
    # Clear in-memory cache
    if key_metadata.key_identifier in crypto_provider._private_keys:
        del crypto_provider._private_keys[key_metadata.key_identifier]

    with pytest.raises(Exception, match="not available locally"):
        await service.activate_key(key_metadata.id, test_admin.id)