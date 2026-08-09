import uuid
from datetime import date
from io import BytesIO
from typing import Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exam import Exam, ExamStatus
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
from app.models.subject import Subject, SubjectStatus
from app.models.user import User


async def _get_superuser_headers(client: AsyncClient) -> Dict[str, str]:
    """Authenticate as superuser and return authorization headers."""
    login_payload = {
        "email": "admin@examshield.gov.in",
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


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


@pytest.mark.asyncio
async def test_upload_question_paper(
    client: AsyncClient, test_subject: Subject
):
    headers = await _get_superuser_headers(client)
    pdf_content = b"%PDF-1.4 Mock PDF Content"
    file = ("test_paper.pdf", BytesIO(pdf_content), "application/pdf")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": "PHY-101",
        "title": "Physics Set A",
        "description": "Test upload",
    }

    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )

    assert response.status_code == 201
    res_data = response.json()["data"]
    assert res_data["paper_code"] == "PHY-101"
    assert res_data["title"] == "Physics Set A"
    assert res_data["version"] == 1
    assert res_data["status"] == QuestionPaperStatus.UPLOADED
    assert res_data["file_size"] == len(pdf_content)
    assert res_data["sha256_hash"] is not None


@pytest.mark.asyncio
async def test_upload_duplicate_increments_version(
    client: AsyncClient, test_subject: Subject, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    pdf_content = b"%PDF-1.4 Mock PDF Content V2"
    file = ("math_v2.pdf", BytesIO(pdf_content), "application/pdf")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": test_paper.paper_code,  # Duplicate code
        "title": "Mathematics Base Updated",
    }

    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )

    assert response.status_code == 201
    res_data = response.json()["data"]
    assert res_data["paper_code"] == test_paper.paper_code
    assert res_data["version"] == 2  # Automatically incremented!


@pytest.mark.asyncio
async def test_upload_invalid_file_type(
    client: AsyncClient, test_subject: Subject
):
    headers = await _get_superuser_headers(client)
    txt_content = b"This is a text file, not a PDF"
    file = ("test.txt", BytesIO(txt_content), "text/plain")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": "CHEM-101",
        "title": "Chemistry",
    }

    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )

    assert response.status_code == 400
    assert "PDF" in response.json()["message"]


@pytest.mark.asyncio
async def test_get_question_papers(
    client: AsyncClient, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    response = await client.get(
        "/api/v1/question-papers",
        headers=headers,
    )
    assert response.status_code == 200
    res_data = response.json()
    assert len(res_data["data"]) >= 1
    assert res_data["data"][0]["paper_code"] == test_paper.paper_code


@pytest.mark.asyncio
async def test_get_question_paper_versions(
    client: AsyncClient, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    response = await client.get(
        f"/api/v1/question-papers/{test_paper.id}/versions",
        headers=headers,
    )
    assert response.status_code == 200
    res_data = response.json()["data"]
    assert len(res_data) >= 1
    assert res_data[0]["version"] == test_paper.version


@pytest.mark.asyncio
async def test_update_question_paper_status(
    client: AsyncClient, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    response = await client.put(
        f"/api/v1/question-papers/{test_paper.id}",
        headers=headers,
        json={"status": QuestionPaperStatus.UNDER_REVIEW},
    )
    assert response.status_code == 200
    assert response.json()["data"]["status"] == QuestionPaperStatus.UNDER_REVIEW


@pytest.mark.asyncio
async def test_update_invalid_status_transition(
    client: AsyncClient, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    # test_paper is in UPLOADED. Cannot transition directly to ARCHIVED.
    response = await client.put(
        f"/api/v1/question-papers/{test_paper.id}",
        headers=headers,
        json={"status": QuestionPaperStatus.ARCHIVED},
    )
    assert response.status_code == 400
    assert "Invalid status transition" in response.json()["message"]


@pytest.mark.asyncio
async def test_delete_question_paper(
    client: AsyncClient, test_paper: QuestionPaper
):
    headers = await _get_superuser_headers(client)
    response = await client.delete(
        f"/api/v1/question-papers/{test_paper.id}",
        headers=headers,
    )
    assert response.status_code == 200

    # Verify it is deleted
    get_response = await client.get(
        f"/api/v1/question-papers/{test_paper.id}",
        headers=headers,
    )
    assert get_response.status_code == 404
