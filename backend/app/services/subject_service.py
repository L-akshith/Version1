"""
ExamShield - Subject Service

Business logic for subject management including creation, status transitions,
validation, and audit logging.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.audit_log import AuditLog
from app.models.subject import SubjectStatus
from app.repositories.exam_repository import ExamRepository
from app.repositories.subject_repository import SubjectRepository
from app.schemas.subject import (
    SubjectCreate,
    SubjectResponse,
    SubjectStatistics,
    SubjectUpdate,
)

logger = logging.getLogger("examshield.subject_service")


class SubjectService:
    """
    Service layer for subject management operations.

    Implements subject CRUD, status lifecycle enforcement, audit logging,
    and validation following the Clean Architecture pattern.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._subject_repo = SubjectRepository(session)
        self._exam_repo = ExamRepository(session)

    # ── Private Helpers ──────────────────────────────────────────

    def _to_response(self, subject: Any) -> SubjectResponse:
        """Convert a Subject model instance to a SubjectResponse schema."""
        return SubjectResponse.model_validate({
            "id": subject.id,
            "exam_id": subject.exam_id,
            "subject_code": subject.subject_code,
            "subject_name": subject.subject_name,
            "language": subject.language,
            "description": subject.description,
            "status": subject.status,
            "created_by": subject.created_by,
            "exam_name": subject.exam_name,
            "creator_name": subject.creator_name,
            "created_at": subject.created_at,
            "updated_at": subject.updated_at,
        })

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry for a subject operation."""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="subjects",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    async def _validate_exam_exists(self, exam_id: uuid.UUID) -> None:
        """Validate that the specified exam exists."""
        exists = await self._exam_repo.exists(exam_id)
        if not exists:
            raise NotFoundException(
                message=f"Exam with ID '{exam_id}' not found"
            )

    # ── Public API ───────────────────────────────────────────────

    async def create_subject(
        self,
        request: SubjectCreate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> SubjectResponse:
        """
        Create a new subject within an exam.

        Args:
            request: Subject creation data.
            user_id: UUID of the creating user.
            ip_address: Client IP for audit trail.

        Returns:
            SubjectResponse with the newly created subject.

        Raises:
            NotFoundException: If the parent exam does not exist.
            ConflictException: If the subject code is already taken within the exam.
        """
        await self._validate_exam_exists(request.exam_id)

        if await self._subject_repo.subject_code_exists(
            request.exam_id, request.subject_code
        ):
            raise ConflictException(
                message=(
                    f"Subject code '{request.subject_code}' is already in use "
                    f"within this exam"
                )
            )

        subject_data: Dict[str, Any] = {
            "exam_id": request.exam_id,
            "subject_code": request.subject_code,
            "subject_name": request.subject_name,
            "language": request.language,
            "description": request.description,
            "status": SubjectStatus.DRAFT,
            "created_by": user_id,
        }

        subject = await self._subject_repo.create(subject_data)
        subject = await self._subject_repo.get_with_relations(subject.id)

        await self._create_audit_entry(
            user_id=user_id,
            action="subject_created",
            resource_id=str(subject.id),
            details={
                "subject_code": subject.subject_code,
                "subject_name": subject.subject_name,
                "exam_id": str(subject.exam_id),
            },
            ip_address=ip_address,
        )

        return self._to_response(subject)

    async def get_subject(self, subject_id: uuid.UUID) -> SubjectResponse:
        """
        Retrieve a single subject by ID.

        Args:
            subject_id: The UUID of the subject to retrieve.

        Returns:
            SubjectResponse with the subject data.

        Raises:
            NotFoundException: If the subject does not exist.
        """
        subject = await self._subject_repo.get_with_relations(subject_id)
        if subject is None:
            raise NotFoundException(
                message=f"Subject with ID '{subject_id}' not found"
            )
        return self._to_response(subject)

    async def list_subjects(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        exam_id: Optional[uuid.UUID] = None,
    ) -> List[SubjectResponse]:
        """
        Retrieve a filtered, paginated list of subjects.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            search: Optional search term.
            exam_id: Optional exam filter.

        Returns:
            List of SubjectResponse objects.
        """
        if status and status not in SubjectStatus.ALL:
            raise BadRequestException(
                message=(
                    f"Invalid status '{status}'. "
                    f"Allowed: {', '.join(sorted(SubjectStatus.ALL))}"
                )
            )

        subjects = await self._subject_repo.list_subjects(
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            exam_id=exam_id,
        )
        return [self._to_response(subject) for subject in subjects]

    async def list_by_exam(
        self,
        exam_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
    ) -> List[SubjectResponse]:
        """
        Retrieve all subjects belonging to a specific exam.

        Args:
            exam_id: UUID of the parent exam.
            skip: Number of records to skip.
            limit: Maximum number of records to return.

        Returns:
            List of SubjectResponse objects.

        Raises:
            NotFoundException: If the exam does not exist.
        """
        await self._validate_exam_exists(exam_id)

        subjects = await self._subject_repo.get_by_exam(
            exam_id=exam_id,
            skip=skip,
            limit=limit,
        )
        return [self._to_response(subject) for subject in subjects]

    async def count_subjects(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        exam_id: Optional[uuid.UUID] = None,
    ) -> int:
        """Return the count of subjects matching the given filters."""
        return await self._subject_repo.count_filtered(
            status=status,
            search=search,
            exam_id=exam_id,
        )

    async def update_subject(
        self,
        subject_id: uuid.UUID,
        update_data: SubjectUpdate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> SubjectResponse:
        """
        Update an existing subject.

        Args:
            subject_id: UUID of the subject to update.
            update_data: Fields to update.
            user_id: UUID of the user performing the update.
            ip_address: Client IP for audit trail.

        Returns:
            SubjectResponse with updated subject data.

        Raises:
            NotFoundException: If the subject does not exist.
            BadRequestException: If the subject is archived or an invalid
                                 status transition is attempted.
        """
        subject = await self._subject_repo.get_with_relations(subject_id)
        if subject is None:
            raise NotFoundException(
                message=f"Subject with ID '{subject_id}' not found"
            )

        if subject.status == SubjectStatus.ARCHIVED:
            raise BadRequestException(
                message="Cannot modify an archived subject"
            )

        data: Dict[str, Any] = update_data.model_dump(exclude_unset=True)

        # Handle status transition validation
        if "status" in data:
            new_status = data["status"]
            if new_status not in SubjectStatus.ALL:
                raise BadRequestException(
                    message=(
                        f"Invalid status '{new_status}'. "
                        f"Allowed: {', '.join(sorted(SubjectStatus.ALL))}"
                    )
                )
            if not SubjectStatus.is_valid_transition(subject.status, new_status):
                allowed_next = SubjectStatus.TRANSITIONS.get(subject.status, set())
                raise BadRequestException(
                    message=(
                        f"Invalid status transition from '{subject.status}' "
                        f"to '{new_status}'. "
                        f"Allowed next: {', '.join(sorted(allowed_next)) or 'none'}"
                    )
                )

            # Archive validation placeholder for future Question Papers
            if new_status == SubjectStatus.ARCHIVED:
                logger.info(
                    "Archive validation: Question Paper check will be enforced "
                    "when the Question Papers module is implemented. "
                    "Subject ID: %s",
                    subject_id,
                )

        if not data:
            return self._to_response(subject)

        await self._subject_repo.update(subject_id, data)
        updated_subject = await self._subject_repo.get_with_relations(subject_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="subject_updated",
            resource_id=str(subject_id),
            details={
                "updated_fields": list(data.keys()),
                "subject_code": subject.subject_code,
                "exam_id": str(subject.exam_id),
            },
            ip_address=ip_address,
        )

        return self._to_response(updated_subject)

    async def delete_subject(
        self,
        subject_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Delete a subject by ID.

        Args:
            subject_id: UUID of the subject to delete.
            user_id: UUID of the user performing the deletion.
            ip_address: Client IP for audit trail.

        Returns:
            True if the subject was deleted.

        Raises:
            NotFoundException: If the subject does not exist.
            BadRequestException: If the subject is archived.
        """
        subject = await self._subject_repo.get_by_id(subject_id)
        if subject is None:
            raise NotFoundException(
                message=f"Subject with ID '{subject_id}' not found"
            )

        if subject.status == SubjectStatus.ARCHIVED:
            raise BadRequestException(
                message="Cannot delete an archived subject. "
                "Archived subjects are retained for audit compliance."
            )

        subject_code = subject.subject_code
        exam_id = str(subject.exam_id)
        deleted = await self._subject_repo.delete(subject_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="subject_deleted",
            resource_id=str(subject_id),
            details={
                "subject_code": subject_code,
                "exam_id": exam_id,
            },
            ip_address=ip_address,
        )

        return deleted

    async def get_statistics(self) -> SubjectStatistics:
        """
        Retrieve subject statistics grouped by status.

        Returns:
            SubjectStatistics with counts by status.
        """
        status_counts = await self._subject_repo.count_by_status()
        total = await self._subject_repo.count()

        return SubjectStatistics(
            total=total,
            draft=status_counts.get(SubjectStatus.DRAFT, 0),
            active=status_counts.get(SubjectStatus.ACTIVE, 0),
            archived=status_counts.get(SubjectStatus.ARCHIVED, 0),
        )
