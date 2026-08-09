"""
ExamShield - Question Paper Service

Business logic for question paper upload, validation, hashing,
version management, status transitions, and audit logging.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.exceptions.api_exception import (
    BadRequestException,
    NotFoundException,
)
from app.models.audit_log import AuditLog
from app.models.question_paper import QuestionPaperStatus
from app.repositories.question_paper_repository import QuestionPaperRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.question_paper import (
    QuestionPaperResponse,
    QuestionPaperStatistics,
    QuestionPaperUpdate,
    QuestionPaperUpload,
    QuestionPaperVersionResponse,
)
from app.storage.storage_interface import StorageInterface
from app.utils.hash_service import HashService

logger = logging.getLogger("examshield.question_paper_service")
settings = get_settings()


class QuestionPaperService:
    """
    Service layer for question paper management operations.

    Implements the secure upload pipeline (validation, storage, hashing),
    version control, status lifecycle enforcement, and audit logging
    following the Clean Architecture pattern.
    """

    def __init__(
        self,
        session: AsyncSession,
        storage_provider: StorageInterface,
    ) -> None:
        self._session = session
        self._storage_provider = storage_provider
        self._paper_repo = QuestionPaperRepository(session)
        self._subject_repo = SubjectRepository(session)
        self._hash_service = HashService()

    # ── Private Helpers ──────────────────────────────────────────

    def _to_response(self, paper: Any) -> QuestionPaperResponse:
        """Convert a QuestionPaper model instance to a QuestionPaperResponse schema."""
        return QuestionPaperResponse.model_validate({
            "id": paper.id,
            "subject_id": paper.subject_id,
            "paper_code": paper.paper_code,
            "title": paper.title,
            "version": paper.version,
            "description": paper.description,
            "status": paper.status,
            "file_name": paper.file_name,
            "original_file_name": paper.original_file_name,
            "storage_path": paper.storage_path,
            "mime_type": paper.mime_type,
            "file_size": paper.file_size,
            "sha256_hash": paper.sha256_hash,
            "uploaded_by": paper.uploaded_by,
            "approved_by": paper.approved_by,
            "upload_time": paper.upload_time,
            "subject_name": paper.subject_name,
            "exam_name": paper.exam_name,
            "uploader_name": paper.uploader_name,
            "approver_name": paper.approver_name,
            "created_at": paper.created_at,
            "updated_at": paper.updated_at,
        })

    def _to_version_response(self, paper: Any) -> QuestionPaperVersionResponse:
        """Convert a QuestionPaper model to a QuestionPaperVersionResponse."""
        return QuestionPaperVersionResponse.model_validate({
            "id": paper.id,
            "version": paper.version,
            "status": paper.status,
            "file_name": paper.file_name,
            "original_file_name": paper.original_file_name,
            "file_size": paper.file_size,
            "sha256_hash": paper.sha256_hash,
            "uploaded_by": paper.uploaded_by,
            "uploader_name": paper.uploader_name,
            "upload_time": paper.upload_time,
            "created_at": paper.created_at,
        })

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry for a question paper operation."""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="question_papers",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    async def _validate_subject_exists(self, subject_id: uuid.UUID) -> None:
        """Validate that the specified subject exists."""
        exists = await self._subject_repo.exists(subject_id)
        if not exists:
            raise NotFoundException(
                message=f"Subject with ID '{subject_id}' not found"
            )

    async def _validate_file(self, file: UploadFile) -> None:
        """
        Validate the uploaded file (extension, MIME type, size).
        """
        if not file.filename:
            raise BadRequestException(message="Filename is missing")

        ext = file.filename.split(".")[-1].lower()
        if ext != "pdf":
            raise BadRequestException(message="Only PDF files are supported")

        if file.content_type != "application/pdf":
            raise BadRequestException(message="File MIME type must be application/pdf")

        # Read file to check size and content
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise BadRequestException(message="Uploaded file is empty")

        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_bytes:
            raise BadRequestException(
                message=f"File size exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB limit"
            )

        # Reset pointer for subsequent reads
        await file.seek(0)

    # ── Public API ───────────────────────────────────────────────

    async def upload_paper(
        self,
        upload_data: QuestionPaperUpload,
        file: UploadFile,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> QuestionPaperResponse:
        """
        Secure upload pipeline for a question paper.
        Validates the file, increments version, stores the file, generates hash,
        persists metadata, and creates an audit log.
        """
        await self._validate_subject_exists(upload_data.subject_id)
        await self._validate_file(file)

        # 1. Determine version
        latest_version = await self._paper_repo.latest_version(
            upload_data.subject_id,
            upload_data.paper_code
        )
        new_version = latest_version + 1

        # 2. Prepare file data and filenames
        file_content = await file.read()
        file_size = len(file_content)
        original_filename = file.filename or "unknown.pdf"
        
        # System filename: <paper_code>_v<version>_<uuid>.pdf
        file_uuid = str(uuid.uuid4())[:8]
        system_filename = f"{upload_data.paper_code}_v{new_version}_{file_uuid}.pdf"
        destination_path = f"{upload_data.subject_id}/{system_filename}"

        # 3. Store file via abstracted StorageInterface
        storage_path = await self._storage_provider.save(file_content, destination_path)

        # 4. Generate SHA-256 hash for integrity
        file_hash = self._hash_service.generate_sha256(file_content)

        # 5. Create database record
        paper_data: Dict[str, Any] = {
            "subject_id": upload_data.subject_id,
            "paper_code": upload_data.paper_code,
            "title": upload_data.title,
            "version": new_version,
            "description": upload_data.description,
            "status": QuestionPaperStatus.UPLOADED,  # Initial status
            "file_name": system_filename,
            "original_file_name": original_filename,
            "storage_path": storage_path,
            "mime_type": file.content_type or "application/pdf",
            "file_size": file_size,
            "sha256_hash": file_hash,
            "uploaded_by": user_id,
        }

        paper = await self._paper_repo.create(paper_data)
        paper = await self._paper_repo.get_with_relations(paper.id)

        # 6. Generate Audit Log
        action = "paper_uploaded" if new_version == 1 else "paper_version_uploaded"
        await self._create_audit_entry(
            user_id=user_id,
            action=action,
            resource_id=str(paper.id),
            details={
                "paper_code": paper.paper_code,
                "version": paper.version,
                "subject_id": str(paper.subject_id),
                "sha256_hash": paper.sha256_hash,
                "file_size": paper.file_size,
            },
            ip_address=ip_address,
        )

        return self._to_response(paper)

    async def get_paper(self, paper_id: uuid.UUID) -> QuestionPaperResponse:
        """
        Retrieve a single question paper by ID.
        """
        paper = await self._paper_repo.get_with_relations(paper_id)
        if paper is None:
            raise NotFoundException(
                message=f"Question Paper with ID '{paper_id}' not found"
            )
        return self._to_response(paper)

    async def list_papers(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        subject_id: Optional[uuid.UUID] = None,
    ) -> List[QuestionPaperResponse]:
        """
        Retrieve a filtered, paginated list of question papers.
        """
        if status and status not in QuestionPaperStatus.ALL:
            raise BadRequestException(
                message=(
                    f"Invalid status '{status}'. "
                    f"Allowed: {', '.join(sorted(QuestionPaperStatus.ALL))}"
                )
            )

        papers = await self._paper_repo.list_papers(
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            subject_id=subject_id,
        )
        return [self._to_response(paper) for paper in papers]

    async def get_versions(
        self, paper_id: uuid.UUID
    ) -> List[QuestionPaperVersionResponse]:
        """
        Retrieve all versions of a specific question paper.
        Uses the provided paper ID to find its subject and paper_code,
        then fetches all matching versions.
        """
        paper = await self._paper_repo.get_by_id(paper_id)
        if paper is None:
            raise NotFoundException(
                message=f"Question Paper with ID '{paper_id}' not found"
            )

        versions = await self._paper_repo.get_versions(
            subject_id=paper.subject_id,
            paper_code=paper.paper_code
        )
        
        return [self._to_version_response(v) for v in versions]

    async def count_papers(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        subject_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Return the count of papers matching the given filters."""
        return await self._paper_repo.count_filtered(
            status=status,
            search=search,
            subject_id=subject_id,
        )

    async def update_paper(
        self,
        paper_id: uuid.UUID,
        update_data: QuestionPaperUpdate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> QuestionPaperResponse:
        """
        Update an existing question paper's metadata or status.
        Enforces strict status transition rules.
        """
        paper = await self._paper_repo.get_with_relations(paper_id)
        if paper is None:
            raise NotFoundException(
                message=f"Question Paper with ID '{paper_id}' not found"
            )

        data: Dict[str, Any] = update_data.model_dump(exclude_unset=True)

        if "status" in data:
            new_status = data["status"]
            if new_status not in QuestionPaperStatus.ALL:
                raise BadRequestException(
                    message=(
                        f"Invalid status '{new_status}'. "
                        f"Allowed: {', '.join(sorted(QuestionPaperStatus.ALL))}"
                    )
                )
            if not QuestionPaperStatus.is_valid_transition(paper.status, new_status):
                allowed_next = QuestionPaperStatus.TRANSITIONS.get(paper.status, set())
                raise BadRequestException(
                    message=(
                        f"Invalid status transition from '{paper.status}' "
                        f"to '{new_status}'. "
                        f"Allowed next: {', '.join(sorted(allowed_next)) or 'none'}"
                    )
                )
            
            # Record who approved it if transitioning to APPROVED
            if new_status == QuestionPaperStatus.APPROVED:
                data["approved_by"] = user_id

        if not data:
            return self._to_response(paper)

        await self._paper_repo.update(paper_id, data)
        updated_paper = await self._paper_repo.get_with_relations(paper_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="paper_updated",
            resource_id=str(paper_id),
            details={
                "updated_fields": list(data.keys()),
                "paper_code": paper.paper_code,
                "version": paper.version,
            },
            ip_address=ip_address,
        )

        return self._to_response(updated_paper)

    async def delete_paper(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Delete a question paper.
        Business rule: Papers in 'approved' or 'archived' status cannot be deleted.
        """
        paper = await self._paper_repo.get_by_id(paper_id)
        if paper is None:
            raise NotFoundException(
                message=f"Question Paper with ID '{paper_id}' not found"
            )

        if paper.status in (QuestionPaperStatus.APPROVED, QuestionPaperStatus.ARCHIVED):
            raise BadRequestException(
                message=f"Cannot delete a paper in '{paper.status}' status. "
                        "It must be retained for audit compliance."
            )

        paper_code = paper.paper_code
        version = paper.version
        
        # Delete file from storage
        await self._storage_provider.delete(paper.storage_path)
        
        deleted = await self._paper_repo.delete(paper_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="paper_deleted",
            resource_id=str(paper_id),
            details={
                "paper_code": paper_code,
                "version": version,
                "subject_id": str(paper.subject_id),
            },
            ip_address=ip_address,
        )

        return deleted

    async def get_statistics(self) -> QuestionPaperStatistics:
        """
        Retrieve question paper statistics grouped by status.
        """
        status_counts = await self._paper_repo.count_by_status()
        total = await self._paper_repo.count()

        return QuestionPaperStatistics(
            total=total,
            draft=status_counts.get(QuestionPaperStatus.DRAFT, 0),
            uploaded=status_counts.get(QuestionPaperStatus.UPLOADED, 0),
            under_review=status_counts.get(QuestionPaperStatus.UNDER_REVIEW, 0),
            approved=status_counts.get(QuestionPaperStatus.APPROVED, 0),
            rejected=status_counts.get(QuestionPaperStatus.REJECTED, 0),
            archived=status_counts.get(QuestionPaperStatus.ARCHIVED, 0),
        )
