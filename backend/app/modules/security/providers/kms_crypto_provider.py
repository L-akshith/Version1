"""
ExamShield - AWS KMS Cryptographic Key Provider

Implements CryptoKeyProvider using AWS Key Management Service (KMS)
for asymmetric RSA-4096 / RSAES_OAEP_SHA_256 operations.

Production master-key wrapping and decryption rely on KMS Hardware
Security Modules (HSMs) rather than local PEM files.
"""

import logging
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat

from app.modules.security.interfaces.crypto_key_provider import CryptoKeyProvider

logger = logging.getLogger("examshield.crypto.kms")

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class AWSKMSCryptoKeyProvider(CryptoKeyProvider):
    """
    Production Cryptographic Key Provider using AWS KMS.

    Supports RSA-4096 key wrapping and unwrapping using RSAES_OAEP_SHA_256.
    """

    def __init__(
        self,
        region_name: str = "us-east-1",
        kms_key_id: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
    ):
        if not BOTO3_AVAILABLE:
            raise RuntimeError(
                "boto3 package is required to use AWSKMSCryptoKeyProvider"
            )

        self.region_name = region_name
        self.kms_key_id = kms_key_id

        client_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.kms_client = boto3.client("kms", **client_kwargs)

    def _resolve_key_id(self, key_identifier: str) -> str:
        """Return the target KMS Key ID or Alias."""
        if key_identifier:
            if key_identifier.startswith("arn:aws:kms:") or key_identifier.startswith("alias/"):
                return key_identifier
            return f"alias/examshield-{key_identifier}"
        if self.kms_key_id:
            return self.kms_key_id
        raise ValueError("No KMS Key Identifier specified")

    async def get_public_key(self, key_identifier: str) -> str:
        """
        Fetch the public key from AWS KMS and return it as a PEM string.
        """
        kms_key = self._resolve_key_id(key_identifier)
        try:
            response = self.kms_client.get_public_key(KeyId=kms_key)
            der_bytes = response["PublicKey"]
            public_key_obj = serialization.load_der_public_key(der_bytes)
            pem_bytes = public_key_obj.public_bytes(
                encoding=Encoding.PEM,
                format=PublicFormat.SubjectPublicKeyInfo,
            )
            return pem_bytes.decode("utf-8")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"KMS get_public_key failed for {kms_key}: {e}")
            raise RuntimeError(f"Cryptographic key '{key_identifier}' not found in KMS: {e}") from e

    async def wrap_key(
        self,
        key_identifier: str,
        plaintext_key: bytes,
    ) -> bytes:
        """
        Wrap a symmetric key using AWS KMS RSAES_OAEP_SHA_256.
        """
        kms_key = self._resolve_key_id(key_identifier)
        try:
            response = self.kms_client.encrypt(
                KeyId=kms_key,
                Plaintext=plaintext_key,
                EncryptionAlgorithm="RSAES_OAEP_SHA_256",
            )
            return response["CiphertextBlob"]
        except (ClientError, BotoCoreError) as e:
            logger.error(f"KMS wrap_key failed for {kms_key}: {e}")
            raise RuntimeError(f"Failed to wrap key using KMS '{key_identifier}': {e}") from e

    async def unwrap_key(
        self,
        key_identifier: str,
        wrapped_key: bytes,
    ) -> bytes:
        """
        Unwrap a symmetric key using AWS KMS RSAES_OAEP_SHA_256.
        """
        kms_key = self._resolve_key_id(key_identifier)
        try:
            response = self.kms_client.decrypt(
                KeyId=kms_key,
                CiphertextBlob=wrapped_key,
                EncryptionAlgorithm="RSAES_OAEP_SHA_256",
            )
            return response["Plaintext"]
        except (ClientError, BotoCoreError) as e:
            logger.error(f"KMS unwrap_key failed for {kms_key}: {e}")
            raise RuntimeError(f"Failed to unwrap key using KMS '{key_identifier}': {e}") from e

    async def generate_rsa_key(
        self,
        key_identifier: str,
    ) -> None:
        """
        Create a new RSA-4096 Customer Managed Key in AWS KMS.
        """
        try:
            response = self.kms_client.create_key(
                KeySpec="RSA_4096",
                KeyUsage="ENCRYPT_DECRYPT",
                Description=f"ExamShield RSA-4096 Master Key ({key_identifier})",
            )
            kms_key_id = response["KeyMetadata"]["KeyId"]
            alias_name = f"alias/examshield-{key_identifier}"
            self.kms_client.create_alias(
                AliasName=alias_name,
                TargetKeyId=kms_key_id,
            )
            logger.info(f"Created KMS Key {kms_key_id} with alias {alias_name}")
        except (ClientError, BotoCoreError) as e:
            logger.error(f"KMS generate_rsa_key failed for {key_identifier}: {e}")
            raise RuntimeError(f"Failed to generate KMS key '{key_identifier}': {e}") from e

    async def validate_key_availability(
        self,
        key_identifier: str,
    ) -> bool:
        """
        Verify that the KMS Key exists and is Enabled.
        """
        try:
            kms_key = self._resolve_key_id(key_identifier)
            response = self.kms_client.describe_key(KeyId=kms_key)
            state = response.get("KeyMetadata", {}).get("KeyState")
            return state == "Enabled"
        except Exception as e:
            logger.warning(f"KMS validate_key_availability check failed for {key_identifier}: {e}")
            return False
