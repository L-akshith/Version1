"""
ExamShield - Pytest Configuration and Fixtures

Sets up an in-memory async SQLite database for fast unit and integration tests.
Overrides FastAPI dependency injection to use the test database session.
"""

import asyncio
from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.session import get_async_session
from app.main import app
from app.database.seed import seed_permissions, seed_roles, seed_superuser
# Import all models so they are registered on Base.metadata for table creation
from app.models.user import User  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.permission import Permission  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.exam import Exam  # noqa: F401
from app.models.subject import Subject  # noqa: F401
from app.models.question_paper import QuestionPaper  # noqa: F401
from app.models.approval_workflow import ApprovalWorkflow  # noqa: F401
from app.models.key_metadata import KeyMetadata  # noqa: F401

# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async engine for test database."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Create tables in test SQLite database
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean session with transactional rollback for each test."""
    connection = await test_engine.connect()
    transaction = await connection.begin()
    
    async_session = async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    session = async_session()
    
    # Seed the temporary database for test scenario
    perms = await seed_permissions(session)
    await seed_roles(session, perms)
    await seed_superuser(session)
    await session.commit()
    
    yield session
    
    await session.close()
    await transaction.rollback()
    await connection.close()

@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTPX AsyncClient configured to call the FastAPI app."""
    
    def override_get_db():
        yield db_session
        
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(
        app=app,
        base_url="http://test",
    ) as ac:
        yield ac
        
    app.dependency_overrides.clear()


import uuid
from datetime import date
from sqlalchemy import select
from app.models.user import User
from app.models.exam import Exam, ExamStatus
from app.models.subject import Subject, SubjectStatus
from app.models.question_paper import QuestionPaper, QuestionPaperStatus

@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> User:
    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    return result.scalar_one()

@pytest_asyncio.fixture
async def test_exam(db_session: AsyncSession, test_admin: User) -> Exam:
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="QP-TEST-EXAM",
        exam_name="QP Test Exam",
        conducting_authority="Test Auth",
        year=2028,
        exam_date=date(2028, 6, 1),
        status=ExamStatus.ACTIVE,
        created_by=test_admin.id,
    )
    db_session.add(exam)
    await db_session.commit()
    await db_session.refresh(exam)
    return exam

@pytest_asyncio.fixture
async def test_subject(db_session: AsyncSession, test_admin: User, test_exam: Exam) -> Subject:
    subject = Subject(
        id=uuid.uuid4(),
        exam_id=test_exam.id,
        subject_code="QP-SUB",
        subject_name="QP Subject",
        language="English",
        status=SubjectStatus.ACTIVE,
        created_by=test_admin.id,
    )
    db_session.add(subject)
    await db_session.commit()
    await db_session.refresh(subject)
    return subject

@pytest_asyncio.fixture
async def test_paper(db_session: AsyncSession, test_admin: User, test_subject: Subject) -> QuestionPaper:
    paper = QuestionPaper(
        id=uuid.uuid4(),
        subject_id=test_subject.id,
        paper_code="MATH-101",
        title="Mathematics Base",
        version=1,
        status=QuestionPaperStatus.UPLOADED,
        file_name="MATH-101_v1_uuid.pdf",
        original_file_name="math.pdf",
        storage_path="path/to/math.pdf",
        mime_type="application/pdf",
        file_size=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        uploaded_by=test_admin.id,
    )
    db_session.add(paper)
    await db_session.commit()
    await db_session.refresh(paper)
    return paper
