import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam, ExamStatus
from app.models.subject import Subject, SubjectStatus
from app.models.user import User


async def _get_superuser_headers(client: AsyncClient) -> dict:
    """Authenticate as superuser and return authorization headers."""
    login_payload = {
        "email": "admin@examshield.gov.in",
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


import pytest_asyncio

@pytest_asyncio.fixture
async def test_exam(db_session: AsyncSession) -> Exam:
    """Create a test exam."""
    from sqlalchemy import select
    from app.models.user import User
    
    stmt = select(User).where(User.email == "admin@examshield.gov.in")
    result = await db_session.execute(stmt)
    admin = result.scalar_one()

    import uuid
    from datetime import date, timedelta
    exam = Exam(
        id=uuid.uuid4(),
        exam_code="TEST-2027",
        exam_name="Test Exam 2027",
        conducting_authority="NTA",
        year=2027,
        exam_date=date(2027, 5, 1),
        status=ExamStatus.ACTIVE,
        created_by=admin.id,
    )
    db_session.add(exam)
    await db_session.commit()
    await db_session.refresh(exam)
    return exam


@pytest.mark.asyncio
async def test_create_subject(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test creating a new subject."""
    admin_token_headers = await _get_superuser_headers(client)
    response = await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "PHY",
            "subject_name": "Physics",
            "language": "English",
            "description": "Core Physics",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["subject_code"] == "PHY"
    assert data["data"]["subject_name"] == "Physics"
    assert data["data"]["exam_id"] == str(test_exam.id)
    assert data["data"]["status"] == SubjectStatus.DRAFT


@pytest.mark.asyncio
async def test_create_duplicate_subject_code(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test creating a duplicate subject code within the same exam."""
    admin_token_headers = await _get_superuser_headers(client)
    # Create first
    await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "CHEM",
            "subject_name": "Chemistry",
            "language": "English",
        },
    )

    # Try duplicate
    response = await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "CHEM",
            "subject_name": "Organic Chemistry",
            "language": "English",
        },
    )
    assert response.status_code == 409
    assert "already in use" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_subjects(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test listing subjects."""
    admin_token_headers = await _get_superuser_headers(client)
    # Create a subject
    await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "MATH",
            "subject_name": "Mathematics",
            "language": "English",
        },
    )

    response = await client.get(
        "/api/v1/subjects",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["total"] >= 1
    assert any(s["subject_code"] == "MATH" for s in data["data"])


@pytest.mark.asyncio
async def test_get_subject_by_id(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test getting a subject by ID."""
    admin_token_headers = await _get_superuser_headers(client)
    create_res = await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "BIO",
            "subject_name": "Biology",
            "language": "English",
        },
    )
    subject_id = create_res.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/subjects/{subject_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["subject_code"] == "BIO"


@pytest.mark.asyncio
async def test_update_subject(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test updating a subject."""
    admin_token_headers = await _get_superuser_headers(client)
    create_res = await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "ENG",
            "subject_name": "English Core",
            "language": "English",
        },
    )
    subject_id = create_res.json()["data"]["id"]

    # Update status to active
    response = await client.put(
        f"/api/v1/subjects/{subject_id}",
        headers=admin_token_headers,
        json={"status": SubjectStatus.ACTIVE, "subject_name": "English Adv"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == SubjectStatus.ACTIVE
    assert response.json()["data"]["subject_name"] == "English Adv"


@pytest.mark.asyncio
async def test_delete_subject(
    client: AsyncClient,
    test_exam: Exam,
):
    """Test deleting a subject."""
    admin_token_headers = await _get_superuser_headers(client)
    create_res = await client.post(
        "/api/v1/subjects",
        headers=admin_token_headers,
        json={
            "exam_id": str(test_exam.id),
            "subject_code": "CS",
            "subject_name": "Computer Science",
            "language": "English",
        },
    )
    subject_id = create_res.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/subjects/{subject_id}",
        headers=admin_token_headers,
    )
    assert response.status_code == 200

    # Verify deleted
    get_res = await client.get(
        f"/api/v1/subjects/{subject_id}",
        headers=admin_token_headers,
    )
    assert get_res.status_code == 404
