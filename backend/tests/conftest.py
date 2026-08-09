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
