"""
ExamShield - Exam Service

Business logic for examination lifecycle management including
creation, status transitions, validation, and audit logging.
"""

import uuid
from datetime import date
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import (
    BadRequestException,
    ConflictException,
    NotFoundException,
)
from app.models.audit_log import AuditLog
from app.models.exam import ExamStatus
from app.repositories.exam_repository import ExamRepository
from app.schemas.exam import (
    ExamCreate,
    ExamResponse,
    ExamStatistics,
    ExamUpdate,
)


class ExamService:
    """
    Service layer for examination management operations.

    Implements exam CRUD, status lifecycle enforcement, audit logging,
    and validation following the Clean Architecture pattern.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._exam_repo = ExamRepository(session)

    # ── Private Helpers ──────────────────────────────────────────

    def _to_response(self, exam: Any) -> ExamResponse:
        """Convert an Exam model instance to an ExamResponse schema."""
        return ExamResponse.model_validate({
            "id": exam.id,
            "exam_code": exam.exam_code,
            "exam_name": exam.exam_name,
            "conducting_authority": exam.conducting_authority,
            "year": exam.year,
            "exam_date": exam.exam_date,
            "description": exam.description,
            "status": exam.status,
            "created_by": exam.created_by,
            "creator_name": exam.creator_name,
            "created_at": exam.created_at,
            "updated_at": exam.updated_at,
        })

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """Create an audit log entry for an exam operation."""
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="exams",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    def _validate_exam_date(self, exam_date: date) -> None:
        """Validate that an exam date is not in the past."""
        if exam_date < date.today():
            raise BadRequestException(
                message=f"Exam date '{exam_date}' cannot be in the past"
            )

    # ── Public API ───────────────────────────────────────────────

    async def create_exam(
        self,
        request: ExamCreate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ExamResponse:
        """
        Create a new examination.

        Args:
            request: Exam creation data.
            user_id: UUID of the creating user.
            ip_address: Client IP for audit trail.

        Returns:
            ExamResponse with the newly created exam.

        Raises:
            ConflictException: If the exam code is already taken.
            BadRequestException: If the exam date is in the past.
        """
        if await self._exam_repo.exam_code_exists(request.exam_code):
            raise ConflictException(
                message=f"Exam code '{request.exam_code}' is already in use"
            )

        self._validate_exam_date(request.exam_date)

        exam_data: Dict[str, Any] = {
            "exam_code": request.exam_code,
            "exam_name": request.exam_name,
            "conducting_authority": request.conducting_authority,
            "year": request.year,
            "exam_date": request.exam_date,
            "description": request.description,
            "status": ExamStatus.DRAFT,
            "created_by": user_id,
        }

        exam = await self._exam_repo.create(exam_data)
        exam = await self._exam_repo.get_with_creator(exam.id)

        await self._create_audit_entry(
            user_id=user_id,
            action="exam_created",
            resource_id=str(exam.id),
            details={"exam_code": exam.exam_code, "exam_name": exam.exam_name},
            ip_address=ip_address,
        )

        return self._to_response(exam)

    async def get_exam(self, exam_id: uuid.UUID) -> ExamResponse:
        """
        Retrieve a single exam by ID.

        Args:
            exam_id: The UUID of the exam to retrieve.

        Returns:
            ExamResponse with the exam data.

        Raises:
            NotFoundException: If the exam does not exist.
        """
        exam = await self._exam_repo.get_with_creator(exam_id)
        if exam is None:
            raise NotFoundException(
                message=f"Exam with ID '{exam_id}' not found"
            )
        return self._to_response(exam)

    async def list_exams(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
    ) -> List[ExamResponse]:
        """
        Retrieve a filtered, paginated list of exams.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            status: Optional status filter.
            search: Optional search term.
            year: Optional year filter.

        Returns:
            List of ExamResponse objects.
        """
        if status and status not in ExamStatus.ALL:
            raise BadRequestException(
                message=f"Invalid status '{status}'. Allowed: {', '.join(sorted(ExamStatus.ALL))}"
            )

        exams = await self._exam_repo.list_exams(
            skip=skip,
            limit=limit,
            status=status,
            search=search,
            year=year,
        )
        return [self._to_response(exam) for exam in exams]

    async def count_exams(
        self,
        status: Optional[str] = None,
        search: Optional[str] = None,
        year: Optional[int] = None,
    ) -> int:
        """Return the count of exams matching the given filters."""
        return await self._exam_repo.count_filtered(
            status=status,
            search=search,
            year=year,
        )

    async def update_exam(
        self,
        exam_id: uuid.UUID,
        update_data: ExamUpdate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ExamResponse:
        """
        Update an existing exam.

        Args:
            exam_id: UUID of the exam to update.
            update_data: Fields to update.
            user_id: UUID of the user performing the update.
            ip_address: Client IP for audit trail.

        Returns:
            ExamResponse with updated exam data.

        Raises:
            NotFoundException: If the exam does not exist.
            BadRequestException: If the exam is archived, the date is in the past,
                                 or an invalid status transition is attempted.
        """
        exam = await self._exam_repo.get_with_creator(exam_id)
        if exam is None:
            raise NotFoundException(
                message=f"Exam with ID '{exam_id}' not found"
            )

        if exam.status == ExamStatus.ARCHIVED:
            raise BadRequestException(
                message="Cannot modify an archived examination"
            )

        data: Dict[str, Any] = update_data.model_dump(exclude_unset=True)

        # Handle status transition validation
        if "status" in data:
            new_status = data["status"]
            if new_status not in ExamStatus.ALL:
                raise BadRequestException(
                    message=f"Invalid status '{new_status}'. "
                    f"Allowed: {', '.join(sorted(ExamStatus.ALL))}"
                )
            if not ExamStatus.is_valid_transition(exam.status, new_status):
                raise BadRequestException(
                    message=f"Invalid status transition from '{exam.status}' to '{new_status}'. "
                    f"Allowed next: {', '.join(sorted(ExamStatus.TRANSITIONS.get(exam.status, set()))) or 'none'}"
                )

        # Validate exam date if provided
        if "exam_date" in data and data["exam_date"] is not None:
            self._validate_exam_date(data["exam_date"])

        if not data:
            return self._to_response(exam)

        await self._exam_repo.update(exam_id, data)
        updated_exam = await self._exam_repo.get_with_creator(exam_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="exam_updated",
            resource_id=str(exam_id),
            details={"updated_fields": list(data.keys()), "exam_code": exam.exam_code},
            ip_address=ip_address,
        )

        return self._to_response(updated_exam)

    async def delete_exam(
        self,
        exam_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Delete an exam by ID.

        Args:
            exam_id: UUID of the exam to delete.
            user_id: UUID of the user performing the deletion.
            ip_address: Client IP for audit trail.

        Returns:
            True if the exam was deleted.

        Raises:
            NotFoundException: If the exam does not exist.
            BadRequestException: If the exam is currently active.
        """
        exam = await self._exam_repo.get_by_id(exam_id)
        if exam is None:
            raise NotFoundException(
                message=f"Exam with ID '{exam_id}' not found"
            )

        if exam.status == ExamStatus.ACTIVE:
            raise BadRequestException(
                message="Cannot delete an active examination. "
                "Complete or archive it first."
            )

        exam_code = exam.exam_code
        deleted = await self._exam_repo.delete(exam_id)

        await self._create_audit_entry(
            user_id=user_id,
            action="exam_deleted",
            resource_id=str(exam_id),
            details={"exam_code": exam_code},
            ip_address=ip_address,
        )

        return deleted

    async def get_statistics(self) -> ExamStatistics:
        """
        Retrieve exam statistics grouped by status.

        Returns:
            ExamStatistics with counts by status.
        """
        status_counts = await self._exam_repo.count_by_status()
        total = await self._exam_repo.count()

        return ExamStatistics(
            total=total,
            draft=status_counts.get(ExamStatus.DRAFT, 0),
            scheduled=status_counts.get(ExamStatus.SCHEDULED, 0),
            active=status_counts.get(ExamStatus.ACTIVE, 0),
            completed=status_counts.get(ExamStatus.COMPLETED, 0),
            archived=status_counts.get(ExamStatus.ARCHIVED, 0),
        )
