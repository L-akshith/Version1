"""
ExamShield - Unit Tests for AWS KMS & S3 Providers
"""

from unittest.mock import MagicMock, patch
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

from app.core.config import Settings, get_settings
from app.modules.security.providers.kms_crypto_provider import AWSKMSCryptoKeyProvider
from app.storage.s3_storage import S3StorageProvider


@pytest.mark.asyncio
async def test_kms_provider_wrap_and_unwrap():
    with patch("boto3.client") as mock_boto:
        kms_client = MagicMock()
        mock_boto.return_value = kms_client

        kms_client.encrypt.return_value = {"CiphertextBlob": b"kms_encrypted_blob"}
        kms_client.decrypt.return_value = {"Plaintext": b"raw_aes_key_32bytes_123456789012"}

        provider = AWSKMSCryptoKeyProvider(region_name="us-east-1", kms_key_id="arn:aws:kms:us-east-1:123456789012:key/test-key")

        wrapped = await provider.wrap_key("test-key", b"raw_aes_key_32bytes_123456789012")
        assert wrapped == b"kms_encrypted_blob"
        kms_client.encrypt.assert_called_once()

        unwrapped = await provider.unwrap_key("test-key", b"kms_encrypted_blob")
        assert unwrapped == b"raw_aes_key_32bytes_123456789012"
        kms_client.decrypt.assert_called_once()


@pytest.mark.asyncio
async def test_kms_provider_get_public_key():
    with patch("boto3.client") as mock_boto:
        kms_client = MagicMock()
        mock_boto.return_value = kms_client

        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        der_pub = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.DER,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        kms_client.get_public_key.return_value = {"PublicKey": der_pub}

        provider = AWSKMSCryptoKeyProvider(region_name="us-east-1")
        pem_pub = await provider.get_public_key("test-key")
        assert "BEGIN PUBLIC KEY" in pem_pub
        assert "END PUBLIC KEY" in pem_pub


@pytest.mark.asyncio
async def test_kms_provider_availability():
    with patch("boto3.client") as mock_boto:
        kms_client = MagicMock()
        mock_boto.return_value = kms_client

        kms_client.describe_key.return_value = {"KeyMetadata": {"KeyState": "Enabled"}}
        provider = AWSKMSCryptoKeyProvider(region_name="us-east-1")

        assert await provider.validate_key_availability("test-key") is True

        kms_client.describe_key.return_value = {"KeyMetadata": {"KeyState": "Disabled"}}
        assert await provider.validate_key_availability("test-key") is False


@pytest.mark.asyncio
async def test_s3_storage_provider_operations():
    with patch("boto3.client") as mock_boto:
        s3_client = MagicMock()
        mock_boto.return_value = s3_client

        s3_client.get_object.return_value = {"Body": MagicMock(read=lambda: b"encrypted_paper_payload")}
        s3_client.head_object.return_value = {"ContentLength": 23}

        provider = S3StorageProvider(bucket_name="examshield-papers-prod", prefix="papers")

        # Save
        uri = await provider.save(b"encrypted_paper_payload", "paper123.bin")
        assert uri == "s3://examshield-papers-prod/papers/paper123.bin"
        s3_client.put_object.assert_called_once()

        # Read
        content = await provider.read(uri)
        assert content == b"encrypted_paper_payload"

        # Exists
        assert await provider.exists(uri) is True

        # Delete
        assert await provider.delete(uri) is True
        s3_client.delete_object.assert_called_once()


def test_production_config_fail_fast_validations():
    get_settings.cache_clear()
    with pytest.raises(ValueError, match="explicit, strong JWT_SECRET_KEY"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            JWT_SECRET_KEY="CHANGE-THIS-TO-A-LONG-RANDOM-SECRET-KEY-IN-PRODUCTION",
            CORS_ORIGINS=["http://localhost:3000"],
        )

    with pytest.raises(ValueError, match=r"wildcard '\*' CORS origin"):
        Settings(
            _env_file=None,
            ENVIRONMENT="production",
            DEBUG=False,
            JWT_SECRET_KEY="A-VERY-STRONG-PRODUCTION-JWT-SECRET-KEY-12345",
            CORS_ORIGINS=["*"],
        )
    get_settings.cache_clear()
