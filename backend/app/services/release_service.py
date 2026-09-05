"""
ExamShield - Release Service

Business logic for the secure release process.
Orchestrates verifying release schedules, unwrapping the central AES session key,
and wrapping it for each authorized Examination Center.
"""

import base64
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions.api_exception import BadRequestException, NotFoundException
from app.models.audit_log import AuditLog
from app.models.center_release_key import CenterReleaseKey
from app.models.question_paper import QuestionPaperStatus
from app.models.release_schedule import ReleaseStatus
from app.repositories.center_release_key_repository import CenterReleaseKeyRepository
from app.repositories.examination_center_repository import ExaminationCenterRepository
from app.repositories.question_paper_repository import QuestionPaperRepository
from app.repositories.release_schedule_repository import ReleaseScheduleRepository
from app.schemas.release import ReleaseScheduleCreate, ReleaseScheduleResponse

logger = logging.getLogger("examshield.release_service")

class ReleaseService:
    """Service layer for secure release operations."""

    def __init__(
        self,
        session: AsyncSession,
        crypto_provider: "CryptoKeyProvider",
    ) -> None:
        self._session = session
        self._crypto_provider = crypto_provider
        self._schedule_repo = ReleaseScheduleRepository(session)
        self._center_repo = ExaminationCenterRepository(session)
        self._paper_repo = QuestionPaperRepository(session)
        self._center_key_repo = CenterReleaseKeyRepository(session)

    async def _create_audit_entry(
        self,
        user_id: uuid.UUID,
        action: str,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource="release_schedules",
            resource_id=resource_id,
            details=details or {},
            ip_address=ip_address,
        )
        self._session.add(audit)
        await self._session.flush()

    async def schedule_release(
        self,
        paper_id: uuid.UUID,
        data: ReleaseScheduleCreate,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> ReleaseScheduleResponse:
        """Schedule a paper for release."""
        paper = await self._paper_repo.get_with_relations(paper_id)
        if not paper:
            raise NotFoundException(message=f"Question Paper with ID '{paper_id}' not found")
        
        # Must be in ENCRYPTED state (i.e. successfully approved and locked)
        if paper.status != QuestionPaperStatus.ENCRYPTED:
            raise BadRequestException(
        message=(
            f"Paper must be in '{QuestionPaperStatus.ENCRYPTED}' "
            f"status to schedule. Current status: '{paper.status}'"
        )
    )
            
        if data.release_at <= datetime.now(timezone.utc):
            raise BadRequestException(message="release_at must be in the future")

        existing_schedule = await self._schedule_repo.get_by_paper_id(paper_id)
        if existing_schedule:
            raise BadRequestException(message=f"Release is already scheduled for paper '{paper_id}'")

        schedule = await self._schedule_repo.create({
            "question_paper_id": paper_id,
            "release_at": data.release_at,
            "status": ReleaseStatus.SCHEDULED,
            "scheduled_by": user_id,
        })
        
        # Transition paper to SCHEDULED
        await self._paper_repo.update(paper_id, {"status": QuestionPaperStatus.SCHEDULED})
        
        await self._create_audit_entry(
            user_id=user_id,
            action="release_scheduled",
            resource_id=str(schedule.id),
            details={"paper_id": str(paper_id), "release_at": data.release_at.isoformat()},
            ip_address=ip_address,
        )
        
        return ReleaseScheduleResponse.model_validate(schedule)

    def _wrap_for_center(self, aes_session_key: bytes, public_key_pem: str) -> str:
        """
        Wrap the AES session key using the center's RSA public key.
        """
        public_key = serialization.load_pem_public_key(public_key_pem.encode('utf-8'))
        
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise ValueError("Provided PEM is not an RSA public key")

        wrapped_key = public_key.encrypt(
            aes_session_key,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return base64.b64encode(wrapped_key).decode('utf-8')

    async def execute_release(
        self,
        paper_id: uuid.UUID,
        user_id: uuid.UUID,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Execute the release logic:
        1. Verify schedule and paper status.
        2. Unwrap central AES session key.
        3. For each authorized center, re-wrap the key with the center's public key.
        4. Save CenterReleaseKey records.
        """
        paper = await self._paper_repo.get_with_relations(paper_id)
        if not paper:
            raise NotFoundException(message=f"Question Paper with ID '{paper_id}' not found")
            
        if paper.status != QuestionPaperStatus.SCHEDULED:
            raise BadRequestException(
                message=f"Paper must be in '{QuestionPaperStatus.SCHEDULED}' status to execute release. Current status: '{paper.status}'"
            )

        # Serialize release execution on the schedule row. The worker also
        # locks this row before invoking this service, while this lock protects
        # direct/API executions from racing with another execution path.
        schedule = await self._schedule_repo.get_by_paper_id(
            paper_id,
            for_update=True,
        )
        if not schedule or schedule.status != ReleaseStatus.SCHEDULED:
            raise BadRequestException(message="No valid schedule found for this paper")
            
        release_time = schedule.release_at
        if release_time.tzinfo is None:
            release_time = release_time.replace(tzinfo=timezone.utc)
            
        if release_time > datetime.now(timezone.utc):
            raise BadRequestException(message="Scheduled release time has not yet been reached")

        # Get central metadata
        metadata = paper.encrypted_metadata
        if not metadata:
            raise BadRequestException(message="No encrypted metadata found for paper")
            
        # Unwrap central AES key
        central_wrapped_key = base64.b64decode(metadata.wrapped_key)
        try:
            aes_session_key = await self._crypto_provider.unwrap_key(
                key_identifier=metadata.key_identifier,
                wrapped_key=central_wrapped_key,
            )
        except Exception as e:
            logger.error(f"Failed to unwrap central AES key for paper {paper_id}: {str(e)}")
            raise BadRequestException(message="Failed to unwrap central AES key")
            
        # Get authorized centers for this exam
        exam_id = paper.subject.exam_id
        # We need to fetch the exam and its authorized centers
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        from app.models.exam import Exam
        
        stmt = select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.authorized_centers))
        exam_result = await self._session.execute(stmt)
        exam = exam_result.scalar_one_or_none()
        
        if not exam:
            raise BadRequestException(message="Associated exam not found")
            
        centers = [c for c in exam.authorized_centers if c.status == "active"]
        
        if not centers:
            raise BadRequestException(message="No active authorized examination centers found for this exam")

        wrapped_count = 0
        try:
            for center in centers:
                if not center.public_key_pem or not center.key_identifier:
                    logger.warning(f"Center {center.id} missing public key or identifier. Skipping.")
                    continue
                    
                existing_key = await self._center_key_repo.get_by_center_and_paper(center.id, paper.id)
                if existing_key:
                    logger.info(f"CenterReleaseKey already exists for center {center.id} and paper {paper.id}. Skipping creation.")
                    wrapped_count += 1
                    continue
                    
                center_wrapped_b64 = self._wrap_for_center(aes_session_key, center.public_key_pem)
                
                await self._center_key_repo.create({
                    "examination_center_id": center.id,
                    "question_paper_id": paper.id,
                    "wrapped_key": center_wrapped_b64,
                    "key_identifier": center.key_identifier,
                })
                wrapped_count += 1
                
            if wrapped_count == 0:
                raise BadRequestException(message="Failed to wrap key for any active center")
                
            # Update statuses
            await self._schedule_repo.update(schedule.id, {"status": ReleaseStatus.RELEASED})
            await self._paper_repo.update(paper_id, {"status": QuestionPaperStatus.RELEASED})
            
            await self._create_audit_entry(
                user_id=user_id,
                action="release_completed",
                resource_id=str(schedule.id),
                details={"paper_id": str(paper_id), "centers_wrapped": wrapped_count},
                ip_address=ip_address,
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Release execution failed for paper {paper_id}: {str(e)}")
            # Database transaction will handle rollback for any created center keys
            await self._create_audit_entry(
                user_id=user_id,
                action="release_failed",
                resource_id=str(schedule.id),
                details={"paper_id": str(paper_id), "error": str(e)},
                ip_address=ip_address,
            )
            raise

    async def list_schedules(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
    ) -> List[ReleaseScheduleResponse]:
        """List release schedules."""
        schedules = await self._schedule_repo.list_schedules(
            skip=skip, limit=limit, status=status
        )
        return [ReleaseScheduleResponse.model_validate(s) for s in schedules]

