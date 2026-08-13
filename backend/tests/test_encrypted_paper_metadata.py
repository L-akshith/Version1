"""
ExamShield - Encrypted Paper Metadata Tests
"""

import uuid
import pytest
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.models.exam import Exam, ExamStatus
from app.models.subject import Subject
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.repositories.encrypted_paper_metadata_repository import EncryptedPaperMetadataRepository
from app.models.user import User
from sqlalchemy import select

pytestmark = pytest.mark.asyncio

async def create_prerequisites(db_session: AsyncSession):
    """Helper to create User, Exam, Subject, and QuestionPaper"""
    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    user = (await db_session.execute(stmt)).scalar_one()

    exam = Exam(
        exam_code=f"EXAM-{uuid.uuid4()}",
        exam_name="Test Exam",
        conducting_authority="NTA",
        year=2026,
        exam_date=date(2026, 5, 1),
        status=ExamStatus.DRAFT,
        created_by=user.id
    )
    db_session.add(exam)
    await db_session.flush()

    subject = Subject(
        exam_id=exam.id,
        subject_code=f"SUB-{uuid.uuid4()}",
        subject_name="Test Subject",
        language="English",
        created_by=user.id
    )
    db_session.add(subject)
    await db_session.flush()

    paper = QuestionPaper(
        subject_id=subject.id,
        paper_code=f"PAPER-{uuid.uuid4()}",
        title="Test Paper",
        file_name="test.enc",
        original_file_name="test.pdf",
        storage_path="/secure/test.enc",
        mime_type="application/pdf",
        file_size=1024,
        sha256_hash="hash",
        status=QuestionPaperStatus.DRAFT,
        uploaded_by=user.id
    )
    db_session.add(paper)
    await db_session.flush()

    return paper

async def test_create_encrypted_metadata(db_session: AsyncSession):
    """Test metadata creation, key_identifier persistence, encrypted artifact persistence"""
    repo = EncryptedPaperMetadataRepository(db_session)
    paper = await create_prerequisites(db_session)

    metadata_data = {
        "question_paper_id": paper.id,
        "key_identifier": "rsa-key-v1-test",
        "encryption_algorithm": "AES256_GCM",
        "nonce": "test-nonce-1234",
        "wrapped_key": "wrapped-aes-key-base64",
        "encrypted_storage_path": "/s3/secure/test.enc",
        "encryption_version": 1
    }

    metadata = await repo.create(metadata_data)
    await db_session.flush()

    assert metadata.id is not None
    assert metadata.key_identifier == "rsa-key-v1-test"
    assert metadata.encrypted_storage_path == "/s3/secure/test.enc"
    assert metadata.wrapped_key == "wrapped-aes-key-base64"

    # Test relationship
    fetched = await repo.get_with_paper(metadata.id)
    assert fetched.question_paper is not None
    assert fetched.question_paper.id == paper.id

    # Test reverse relationship from QuestionPaper
    await db_session.refresh(paper)
    assert paper.encrypted_metadata is not None
    assert paper.encrypted_metadata.id == metadata.id

async def test_rejection_of_missing_required_fields(db_session: AsyncSession):
    """Test rejection when required fields are missing"""
    repo = EncryptedPaperMetadataRepository(db_session)
    paper = await create_prerequisites(db_session)

    # Missing wrapped_key
    metadata_data = {
        "question_paper_id": paper.id,
        "key_identifier": "rsa-key-v1-test",
        "encryption_algorithm": "AES256_GCM",
        "nonce": "test-nonce-1234",
        "encrypted_storage_path": "/s3/secure/test.enc",
        "encryption_version": 1
    }

    metadata = EncryptedPaperMetadata(**metadata_data)
    db_session.add(metadata)
    
    with pytest.raises(IntegrityError):
        await db_session.flush()
