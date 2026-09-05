"""
ExamShield - AWS S3 File Storage Provider

Implements StorageInterface using Amazon S3 with SSE-KMS server-side
encryption for question paper object payloads.
"""

import logging
from typing import Optional

from app.storage.storage_interface import StorageInterface

logger = logging.getLogger("examshield.storage.s3")

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False


class S3StorageProvider(StorageInterface):
    """
    AWS S3 storage provider enforcing private access and SSE-KMS encryption.
    """

    def __init__(
        self,
        bucket_name: str,
        region_name: str = "us-east-1",
        prefix: str = "question_papers",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        kms_key_id: Optional[str] = None,
    ) -> None:
        if not BOTO3_AVAILABLE:
            raise RuntimeError("boto3 package is required to use S3StorageProvider")

        self.bucket_name = bucket_name
        self.region_name = region_name
        self.prefix = prefix.strip("/")
        self.kms_key_id = kms_key_id

        client_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            client_kwargs["aws_access_key_id"] = aws_access_key_id
            client_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.s3_client = boto3.client("s3", **client_kwargs)
        logger.info(f"S3StorageProvider initialized for bucket: {bucket_name}")

    def _resolve_key(self, storage_path: str) -> str:
        """Resolve storage_path (either s3://bucket/key or relative key) to clean S3 Key."""
        if storage_path.startswith("s3://"):
            parts = storage_path[5:].split("/", 1)
            if len(parts) == 2:
                return parts[1]
        if storage_path.startswith(f"{self.prefix}/"):
            return storage_path
        return f"{self.prefix}/{storage_path}".strip("/")

    async def save(self, file_data: bytes, destination_path: str) -> str:
        """
        Upload file data to private S3 bucket with server-side encryption.
        """
        s3_key = self._resolve_key(destination_path)
        put_kwargs = {
            "Bucket": self.bucket_name,
            "Key": s3_key,
            "Body": file_data,
        }

        if self.kms_key_id:
            put_kwargs["ServerSideEncryption"] = "aws:kms"
            put_kwargs["SSEKMSKeyId"] = self.kms_key_id
        else:
            put_kwargs["ServerSideEncryption"] = "AES256"

        try:
            self.s3_client.put_object(**put_kwargs)
            storage_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Uploaded S3 object: {storage_uri} ({len(file_data)} bytes)")
            return storage_uri
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 save failed for {s3_key}: {e}")
            raise RuntimeError(f"Failed to upload question paper to S3: {e}") from e

    async def read(self, storage_path: str) -> bytes:
        """
        Download object bytes from private S3 bucket.
        """
        s3_key = self._resolve_key(storage_path)
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return response["Body"].read()
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchKey"):
                raise FileNotFoundError(f"S3 object not found: {storage_path}") from e
            logger.error(f"S3 read failed for {s3_key}: {e}")
            raise RuntimeError(f"Failed to read question paper from S3: {e}") from e
        except BotoCoreError as e:
            logger.error(f"S3 read failed for {s3_key}: {e}")
            raise RuntimeError(f"Failed to read question paper from S3: {e}") from e

    async def delete(self, storage_path: str) -> bool:
        """
        Delete object from S3 bucket.
        """
        s3_key = self._resolve_key(storage_path)
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            logger.info(f"Deleted S3 object: {s3_key}")
            return True
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 delete failed for {s3_key}: {e}")
            return False

    async def exists(self, storage_path: str) -> bool:
        """
        Check if S3 object exists using head_object.
        """
        s3_key = self._resolve_key(storage_path)
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key,
            )
            return True
        except ClientError:
            return False
