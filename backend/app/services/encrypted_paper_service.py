"""
ExamShield - Encrypted Paper Service

Integrates the existing cryptographic components (AES-256-GCM, RSA-OAEP,
HybridEncryptionService, LocalCryptoKeyProvider) with QuestionPaper and
EncryptedPaperMetadata to provide encrypt/decrypt operations for
examination papers.

Security invariants:
    - A NEW AES-256 key is generated for every encryption operation.
    - A NEW GCM nonce is generated for every encryption operation.
    - RSA-OAEP is used only to wrap the AES session key.
    - Plaintext AES keys are NEVER persisted.
    - RSA private keys are NEVER persisted in the database.
    - Raw key material is NEVER logged, returned in API responses, or
      written to audit entries.
    - nonce and wrapped_key are stored as Base64-encoded strings.
"""

import base64
import logging
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import (
    BadRequestException,
    NotFoundException,
)
from app.models.audit_log import AuditLog
from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.modules.security.encryption.aes_gcm import AESGCMEncryptionService
from app.modules.security.interfaces.crypto_key_provider import CryptoKeyProvider
from app.repositories.encrypted_paper_metadata_repository import (
    EncryptedPaperMetadataRepository,
)
from app.storage.storage_interface import StorageInterface
from app.utils.hash_service import HashService

logger = logging.getLogger("examshield.encrypted_paper_service")


@dataclass(frozen=True)
class EncryptionResult:
    """Value object returned after a successful encryption operation."""

    metadata_id: uuid.UUID
    question_paper_id: uuid.UUID
    key_identifier: str
    encryption_algorithm: str
    encrypted_storage_path: str
    encryption_version: int
    ciphertext_sha256: str


class EncryptedPaperService:
    """
    Service for encrypting and decrypting question papers.

    Orchestrates existing AES-256-GCM encryption, RSA-OAEP key wrapping
    via the CryptoKeyProvider, persistent storage via StorageInterface,
    and metadata persistence via EncryptedPaperMetadataRepository.
    """

    ENCRYPTION_ALGORITHM = "AES256_GCM"
    ENCRYPTION_VERSION = 1

    def __init__(
        self,
        session: AsyncSession,
        crypto_provider: CryptoKeyProvider,
        storage_provider: StorageInterface,
    ) -> None:
        self._session = session
        self._crypto_provider = crypto_provider
        self._storage_provider = storage_provider
        self._metadata_repo = EncryptedPaperMetadataRepository(session)
        self._hash_service = HashService()

    # ── Private Helpers ──────────────────────────────────────────

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry. Never includes raw key material."""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="encrypted_papers",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    # ── Public API ───────────────────────────────────────────────

    async def encrypt_question_paper(
        self,
        question_paper_id: uuid.UUID,
        plaintext_content: bytes,
        key_identifier: str,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> EncryptionResult:
        """
        Encrypt a question paper's content and persist the metadata.

        Steps:
            1. Generate a fresh random AES-256 key.
            2. Encrypt content using AES-256-GCM.
            3. Wrap the AES key using RSA-OAEP via the CryptoKeyProvider.
            4. Store the encrypted artifact via StorageInterface.
            5. Persist EncryptedPaperMetadata (nonce + wrapped_key as Base64).
            6. Record an audit entry.

        Args:
            question_paper_id: UUID of the QuestionPaper to encrypt.
            plaintext_content: Raw bytes of the paper content.
            key_identifier: Identifier of the RSA wrapping key.
            user_id: UUID of the user performing the operation.
            ip_address: Optional client IP for audit logging.

        Returns:
            EncryptionResult with metadata about the encrypted artifact.

        Raises:
            BadRequestException: If content is empty.
        """
        if not plaintext_content:
            raise BadRequestException(
                message="Cannot encrypt empty content."
            )

        # Check for existing encryption metadata
        existing = await self._metadata_repo.get_by_question_paper_id(
            question_paper_id
        )
        if existing is not None:
            raise BadRequestException(
                message="Question paper is already encrypted. "
                "Decrypt or remove existing metadata first."
            )

        # Check if wrapping key is available locally
        is_available = await self._crypto_provider.validate_key_availability(key_identifier)
        if not is_available:
            raise BadRequestException(
                message=f"Private key for wrapping key '{key_identifier}' is not available locally."
            )

        # 1. Generate a fresh AES-256 session key
        aes_key = AESGCMEncryptionService.generate_key()

        # 2. Encrypt the paper content with AES-256-GCM
        ciphertext, nonce = AESGCMEncryptionService.encrypt(
            plaintext=plaintext_content,
            key=aes_key,
        )

        # 3. Wrap the AES key using RSA-OAEP via the CryptoKeyProvider
        wrapped_key_bytes = await self._crypto_provider.wrap_key(
            key_identifier=key_identifier,
            plaintext_key=aes_key,
        )

        # 4. Store the encrypted artifact
        encrypted_destination = (
            f"encrypted/{question_paper_id}/{uuid.uuid4()}.enc"
        )
        encrypted_storage_path = await self._storage_provider.save(
            file_data=ciphertext,
            destination_path=encrypted_destination,
        )

        # 5. Compute ciphertext integrity hash
        ciphertext_sha256 = self._hash_service.generate_sha256(ciphertext)

        # 6. Persist EncryptedPaperMetadata
        #    nonce and wrapped_key are Base64-encoded for safe text storage.
        nonce_b64 = base64.b64encode(nonce).decode("ascii")
        wrapped_key_b64 = base64.b64encode(wrapped_key_bytes).decode("ascii")

        metadata_data = {
            "question_paper_id": question_paper_id,
            "key_identifier": key_identifier,
            "encryption_algorithm": self.ENCRYPTION_ALGORITHM,
            "nonce": nonce_b64,
            "wrapped_key": wrapped_key_b64,
            "encrypted_storage_path": encrypted_storage_path,
            "encryption_version": self.ENCRYPTION_VERSION,
        }

        try:
            metadata = await self._metadata_repo.create(metadata_data)
        except Exception:
            # Transaction safety: clean up the stored artifact if
            # metadata persistence fails.
            logger.error(
                "Metadata persistence failed for paper %s; "
                "cleaning up encrypted artifact.",
                question_paper_id,
            )
            await self._storage_provider.delete(encrypted_storage_path)
            raise

        # 7. Audit — no raw key material in details
        await self._create_audit_entry(
            user_id=user_id,
            action="paper_encrypted",
            resource_id=str(question_paper_id),
            details={
                "key_identifier": key_identifier,
                "encryption_algorithm": self.ENCRYPTION_ALGORITHM,
                "encryption_version": self.ENCRYPTION_VERSION,
                "ciphertext_sha256": ciphertext_sha256,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Paper %s encrypted successfully with key '%s'.",
            question_paper_id,
            key_identifier,
        )

        return EncryptionResult(
            metadata_id=metadata.id,
            question_paper_id=question_paper_id,
            key_identifier=key_identifier,
            encryption_algorithm=self.ENCRYPTION_ALGORITHM,
            encrypted_storage_path=encrypted_storage_path,
            encryption_version=self.ENCRYPTION_VERSION,
            ciphertext_sha256=ciphertext_sha256,
        )

    async def decrypt_question_paper(
        self,
        question_paper_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> bytes:
        """
        Decrypt a question paper using its stored metadata.

        Steps:
            1. Retrieve EncryptedPaperMetadata.
            2. Read encrypted artifact from storage.
            3. Decode Base64 nonce and wrapped_key.
            4. Unwrap the AES key via the CryptoKeyProvider.
            5. Decrypt using AES-256-GCM.
            6. Record an audit entry.

        Args:
            question_paper_id: UUID of the QuestionPaper to decrypt.
            user_id: UUID of the user performing the operation.
            ip_address: Optional client IP for audit logging.

        Returns:
            Decrypted plaintext bytes.

        Raises:
            NotFoundException: If no metadata or encrypted artifact exists.
            BadRequestException: If decryption fails (authentication failure).
        """
        # 1. Retrieve metadata
        metadata = await self._metadata_repo.get_by_question_paper_id(
            question_paper_id
        )
        if metadata is None:
            raise NotFoundException(
                message=f"No encryption metadata found for paper '{question_paper_id}'."
            )

        # 2. Read encrypted artifact from storage
        artifact_exists = await self._storage_provider.exists(
            metadata.encrypted_storage_path
        )
        if not artifact_exists:
            raise NotFoundException(
                message=f"Encrypted artifact not found at '{metadata.encrypted_storage_path}'."
            )

        ciphertext = await self._storage_provider.read(
            metadata.encrypted_storage_path
        )

        # 3. Decode Base64 nonce and wrapped_key
        try:
            nonce = base64.b64decode(metadata.nonce)
            wrapped_key_bytes = base64.b64decode(metadata.wrapped_key)
        except Exception as exc:
            raise BadRequestException(
                message="Failed to decode encryption metadata (nonce/wrapped_key)."
            ) from exc

        # 4. Unwrap the AES key via CryptoKeyProvider
        try:
            aes_key = await self._crypto_provider.unwrap_key(
                key_identifier=metadata.key_identifier,
                wrapped_key=wrapped_key_bytes,
            )
        except KeyError as exc:
            raise NotFoundException(
                message=f"Cryptographic key '{metadata.key_identifier}' not found in provider."
            ) from exc
        except Exception as exc:
            raise BadRequestException(
                message="Failed to unwrap AES session key. "
                "The RSA key may be incorrect or corrupted."
            ) from exc

        # 5. Decrypt using AES-256-GCM
        try:
            plaintext = AESGCMEncryptionService.decrypt(
                ciphertext=ciphertext,
                key=aes_key,
                nonce=nonce,
            )
        except ValueError as exc:
            raise BadRequestException(
                message="Decryption authentication failed: "
                "ciphertext, nonce, or wrapped key may have been tampered with."
            ) from exc

        # 6. Audit — no raw key material in details
        await self._create_audit_entry(
            user_id=user_id,
            action="paper_decrypted",
            resource_id=str(question_paper_id),
            details={
                "key_identifier": metadata.key_identifier,
                "encryption_algorithm": metadata.encryption_algorithm,
            },
            ip_address=ip_address,
        )

        logger.info(
            "Paper %s decrypted successfully with key '%s'.",
            question_paper_id,
            metadata.key_identifier,
        )

        return plaintext

    async def get_encrypted_metadata(
        self,
        question_paper_id: uuid.UUID,
    ) -> EncryptedPaperMetadata:
        """
        Retrieve encryption metadata for a question paper.

        Returns metadata only. Never returns raw AES/RSA key material.

        Args:
            question_paper_id: UUID of the QuestionPaper.

        Returns:
            EncryptedPaperMetadata instance.

        Raises:
            NotFoundException: If no metadata exists for the paper.
        """
        metadata = await self._metadata_repo.get_by_question_paper_id(
            question_paper_id
        )
        if metadata is None:
            raise NotFoundException(
                message=f"No encryption metadata found for paper '{question_paper_id}'."
            )
        return metadata
