"""
ExamShield - Exam Management Tests

Tests for exam CRUD operations, status transitions, validation rules,
audit logging, and permission enforcement.
"""

import uuid
from datetime import date, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam, ExamStatus
from app.repositories.exam_repository import ExamRepository
from app.services.exam_service import ExamService

pytestmark = pytest.mark.asyncio


# ── Helpers ──────────────────────────────────────────────────────

async def _get_superuser_headers(client: AsyncClient) -> dict:
    """Authenticate as superuser and return authorization headers."""
    login_payload = {
        "email": "admin@examshield.gov.in",
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _exam_payload(
    exam_code: str = "NEET-2026-PH1",
    exam_name: str = "NEET UG 2026 Phase 1",
    conducting_authority: str = "National Testing Agency",
    year: int = 2026,
    days_ahead: int = 30,
    description: str = "National Eligibility cum Entrance Test for UG medical admissions",
) -> dict:
    """Generate a valid exam creation payload."""
    return {
        "exam_code": exam_code,
        "exam_name": exam_name,
        "conducting_authority": conducting_authority,
        "year": year,
        "exam_date": str(date.today() + timedelta(days=days_ahead)),
        "description": description,
    }


# ── Repository Tests ─────────────────────────────────────────────

async def test_exam_repository_create_and_get(db_session: AsyncSession) -> None:
    """Verify ExamRepository can create and retrieve exams."""
    repo = ExamRepository(db_session)

    # Get a user id from the seeded superuser
    from app.models.user import User
    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    exam_data = {
        "exam_code": "REPO-TEST-001",
        "exam_name": "Repository Test Exam",
        "conducting_authority": "Test Authority",
        "year": 2026,
        "exam_date": date.today() + timedelta(days=60),
        "description": "Testing repository layer",
        "status": ExamStatus.DRAFT,
        "created_by": admin.id,
    }

    exam = await repo.create(exam_data)
    await db_session.flush()

    assert exam.id is not None
    assert exam.exam_code == "REPO-TEST-001"
    assert exam.status == ExamStatus.DRAFT

    # Retrieve by ID
    fetched = await repo.get_by_id(exam.id)
    assert fetched is not None
    assert fetched.exam_name == "Repository Test Exam"

    # Retrieve by code
    by_code = await repo.get_by_exam_code("REPO-TEST-001")
    assert by_code is not None
    assert by_code.id == exam.id

    # Code existence check
    assert await repo.exam_code_exists("REPO-TEST-001") is True
    assert await repo.exam_code_exists("NONEXISTENT") is False


async def test_exam_repository_list_and_count(db_session: AsyncSession) -> None:
    """Verify ExamRepository listing with filters and count operations."""
    repo = ExamRepository(db_session)

    from app.models.user import User
    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    # Create multiple exams
    for i in range(3):
        await repo.create({
            "exam_code": f"LIST-TEST-{i:03d}",
            "exam_name": f"List Test Exam {i}",
            "conducting_authority": "Test Authority",
            "year": 2026,
            "exam_date": date.today() + timedelta(days=30 + i),
            "status": ExamStatus.DRAFT,
            "created_by": admin.id,
        })
    await db_session.flush()

    # List all
    exams = await repo.list_exams(skip=0, limit=100)
    assert len(exams) >= 3

    # Filter by search
    filtered = await repo.list_exams(search="LIST-TEST")
    assert len(filtered) >= 3

    # Count
    count = await repo.count_filtered(search="LIST-TEST")
    assert count >= 3

    # Count by status
    status_counts = await repo.count_by_status()
    assert ExamStatus.DRAFT in status_counts


# ── Service Tests ────────────────────────────────────────────────

async def test_exam_service_create_validates_duplicate_code(
    db_session: AsyncSession,
) -> None:
    """Verify ExamService rejects duplicate exam codes."""
    from app.models.user import User
    from app.schemas.exam import ExamCreate
    from app.exceptions.api_exception import ConflictException

    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    service = ExamService(db_session)

    create_data = ExamCreate(
        exam_code="DUP-SVC-001",
        exam_name="Duplicate Test",
        conducting_authority="Test Authority",
        year=2026,
        exam_date=date.today() + timedelta(days=30),
    )

    await service.create_exam(create_data, admin.id)
    await db_session.flush()

    with pytest.raises(ConflictException, match="already in use"):
        await service.create_exam(create_data, admin.id)


async def test_exam_service_rejects_past_date(db_session: AsyncSession) -> None:
    """Verify ExamService rejects exam dates in the past."""
    from app.models.user import User
    from app.schemas.exam import ExamCreate
    from app.exceptions.api_exception import BadRequestException

    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    service = ExamService(db_session)

    create_data = ExamCreate(
        exam_code="PAST-DATE-001",
        exam_name="Past Date Exam",
        conducting_authority="Test Authority",
        year=2020,
        exam_date=date.today() - timedelta(days=10),
    )

    with pytest.raises(BadRequestException, match="cannot be in the past"):
        await service.create_exam(create_data, admin.id)


async def test_exam_service_status_transitions(db_session: AsyncSession) -> None:
    """Verify ExamService enforces valid status transitions."""
    from app.models.user import User
    from app.schemas.exam import ExamCreate, ExamUpdate
    from app.exceptions.api_exception import BadRequestException

    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    service = ExamService(db_session)

    exam = await service.create_exam(
        ExamCreate(
            exam_code="TRANS-001",
            exam_name="Transition Test",
            conducting_authority="Test Authority",
            year=2026,
            exam_date=date.today() + timedelta(days=60),
        ),
        admin.id,
    )
    await db_session.flush()

    # Draft → Scheduled (valid)
    updated = await service.update_exam(
        exam.id, ExamUpdate(status="scheduled"), admin.id
    )
    assert updated.status == "scheduled"

    # Scheduled → Active (valid)
    updated = await service.update_exam(
        exam.id, ExamUpdate(status="active"), admin.id
    )
    assert updated.status == "active"

    # Active → Draft (invalid)
    with pytest.raises(BadRequestException, match="Invalid status transition"):
        await service.update_exam(
            exam.id, ExamUpdate(status="draft"), admin.id
        )

    # Active → Completed (valid)
    updated = await service.update_exam(
        exam.id, ExamUpdate(status="completed"), admin.id
    )
    assert updated.status == "completed"

    # Completed → Archived (valid)
    updated = await service.update_exam(
        exam.id, ExamUpdate(status="archived"), admin.id
    )
    assert updated.status == "archived"

    # Archived → any (rejected)
    with pytest.raises(BadRequestException, match="Cannot modify an archived"):
        await service.update_exam(
            exam.id, ExamUpdate(status="draft"), admin.id
        )


async def test_exam_service_cannot_delete_active(db_session: AsyncSession) -> None:
    """Verify ExamService prevents deletion of active exams."""
    from app.models.user import User
    from app.schemas.exam import ExamCreate, ExamUpdate
    from app.exceptions.api_exception import BadRequestException

    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    service = ExamService(db_session)

    exam = await service.create_exam(
        ExamCreate(
            exam_code="DEL-ACTIVE-001",
            exam_name="Delete Active Test",
            conducting_authority="Test Authority",
            year=2026,
            exam_date=date.today() + timedelta(days=30),
        ),
        admin.id,
    )
    await db_session.flush()

    # Transition to Active
    await service.update_exam(exam.id, ExamUpdate(status="scheduled"), admin.id)
    await service.update_exam(exam.id, ExamUpdate(status="active"), admin.id)

    with pytest.raises(BadRequestException, match="Cannot delete an active"):
        await service.delete_exam(exam.id, admin.id)


async def test_exam_service_statistics(db_session: AsyncSession) -> None:
    """Verify ExamService returns correct statistics."""
    from app.models.user import User
    from app.schemas.exam import ExamCreate

    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    service = ExamService(db_session)

    await service.create_exam(
        ExamCreate(
            exam_code="STAT-001",
            exam_name="Stats Test Exam",
            conducting_authority="Test Authority",
            year=2026,
            exam_date=date.today() + timedelta(days=45),
        ),
        admin.id,
    )
    await db_session.flush()

    stats = await service.get_statistics()
    assert stats.total >= 1
    assert stats.draft >= 1


# ── API Tests ────────────────────────────────────────────────────

async def test_create_exam_api(client: AsyncClient) -> None:
    """Verify POST /api/v1/exams creates an exam successfully."""
    headers = await _get_superuser_headers(client)
    payload = _exam_payload()

    response = await client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 201
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["exam_code"] == "NEET-2026-PH1"
    assert json_data["data"]["status"] == "draft"
    assert json_data["data"]["creator_name"] is not None


async def test_create_exam_duplicate_code(client: AsyncClient) -> None:
    """Verify creating an exam with a duplicate code returns 409."""
    headers = await _get_superuser_headers(client)
    payload = _exam_payload(exam_code="DUP-API-001")

    await client.post("/api/v1/exams", json=payload, headers=headers)
    response = await client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 409
    assert "already in use" in response.json()["message"]


async def test_list_exams_api(client: AsyncClient) -> None:
    """Verify GET /api/v1/exams returns a paginated list."""
    headers = await _get_superuser_headers(client)

    # Create an exam first
    await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="LIST-API-001"),
        headers=headers,
    )

    response = await client.get("/api/v1/exams", headers=headers)
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["total"] >= 1
    assert len(json_data["data"]) >= 1


async def test_get_exam_by_id_api(client: AsyncClient) -> None:
    """Verify GET /api/v1/exams/{id} returns a specific exam."""
    headers = await _get_superuser_headers(client)

    create_res = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="GET-API-001"),
        headers=headers,
    )
    exam_id = create_res.json()["data"]["id"]

    response = await client.get(f"/api/v1/exams/{exam_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["exam_code"] == "GET-API-001"


async def test_get_exam_not_found(client: AsyncClient) -> None:
    """Verify GET /api/v1/exams/{id} returns 404 for nonexistent ID."""
    headers = await _get_superuser_headers(client)
    fake_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/exams/{fake_id}", headers=headers)
    assert response.status_code == 404


async def test_update_exam_api(client: AsyncClient) -> None:
    """Verify PUT /api/v1/exams/{id} updates exam fields."""
    headers = await _get_superuser_headers(client)

    create_res = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="UPD-API-001"),
        headers=headers,
    )
    exam_id = create_res.json()["data"]["id"]

    update_payload = {"exam_name": "Updated Exam Name", "status": "scheduled"}
    response = await client.put(
        f"/api/v1/exams/{exam_id}", json=update_payload, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["data"]["exam_name"] == "Updated Exam Name"
    assert response.json()["data"]["status"] == "scheduled"


async def test_update_exam_invalid_transition(client: AsyncClient) -> None:
    """Verify PUT /api/v1/exams/{id} rejects invalid status transitions."""
    headers = await _get_superuser_headers(client)

    create_res = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="BAD-TRANS-001"),
        headers=headers,
    )
    exam_id = create_res.json()["data"]["id"]

    # Draft → Active (invalid, must go Draft → Scheduled → Active)
    response = await client.put(
        f"/api/v1/exams/{exam_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["message"]


async def test_delete_exam_api(client: AsyncClient) -> None:
    """Verify DELETE /api/v1/exams/{id} deletes a draft exam."""
    headers = await _get_superuser_headers(client)

    create_res = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="DEL-API-001"),
        headers=headers,
    )
    exam_id = create_res.json()["data"]["id"]

    response = await client.delete(f"/api/v1/exams/{exam_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["success"] is True

    # Confirm it's gone
    get_res = await client.get(f"/api/v1/exams/{exam_id}", headers=headers)
    assert get_res.status_code == 404


async def test_delete_active_exam_rejected(client: AsyncClient) -> None:
    """Verify DELETE /api/v1/exams/{id} rejects deletion of active exams."""
    headers = await _get_superuser_headers(client)

    create_res = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="DEL-ACTIVE-API"),
        headers=headers,
    )
    exam_id = create_res.json()["data"]["id"]

    # Draft → Scheduled → Active
    await client.put(
        f"/api/v1/exams/{exam_id}",
        json={"status": "scheduled"},
        headers=headers,
    )
    await client.put(
        f"/api/v1/exams/{exam_id}",
        json={"status": "active"},
        headers=headers,
    )

    response = await client.delete(f"/api/v1/exams/{exam_id}", headers=headers)
    assert response.status_code == 400
    assert "Cannot delete an active" in response.json()["message"]


async def test_exam_statistics_api(client: AsyncClient) -> None:
    """Verify GET /api/v1/exams/statistics returns aggregated counts."""
    headers = await _get_superuser_headers(client)

    # Create an exam so we have at least one
    await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="STATS-API-001"),
        headers=headers,
    )

    response = await client.get("/api/v1/exams/statistics", headers=headers)
    assert response.status_code == 200
    stats = response.json()["data"]
    assert stats["total"] >= 1
    assert "draft" in stats
    assert "scheduled" in stats
    assert "active" in stats
    assert "completed" in stats
    assert "archived" in stats


async def test_exam_api_requires_auth(client: AsyncClient) -> None:
    """Verify exam endpoints require authentication."""
    response = await client.get("/api/v1/exams")
    assert response.status_code == 403  # HTTPBearer returns 403 when no header


async def test_observer_cannot_create_exam(client: AsyncClient) -> None:
    """Verify Observer role lacks exams:create permission."""
    # Register as observer
    reg_payload = {
        "email": "observer_exam@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Observer User",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post("/api/v1/auth/login", json={
        "email": "observer_exam@examshield.gov.in",
        "password": "SecurePassword123!",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="OBS-TEST-001"),
        headers=headers,
    )
    assert response.status_code == 403


async def test_observer_can_read_exams(client: AsyncClient) -> None:
    """Verify Observer role has exams:read permission."""
    admin_headers = await _get_superuser_headers(client)

    # Create an exam as admin
    await client.post(
        "/api/v1/exams",
        json=_exam_payload(exam_code="OBS-READ-001"),
        headers=admin_headers,
    )

    # Login as observer
    await client.post("/api/v1/auth/register", json={
        "email": "obs_read@examshield.gov.in",
        "password": "SecurePassword123!",
        "full_name": "Observer Reader",
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "email": "obs_read@examshield.gov.in",
        "password": "SecurePassword123!",
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.get("/api/v1/exams", headers=headers)
    assert response.status_code == 200
