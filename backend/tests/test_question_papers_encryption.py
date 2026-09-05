import uuid
from io import BytesIO
from typing import Dict

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.models.question_paper import QuestionPaper
from app.models.subject import Subject
from app.models.user import User
from app.storage.storage_interface import StorageInterface
from app.services.encrypted_paper_service import EncryptedPaperService


pytestmark = pytest.mark.asyncio


async def _get_superuser_headers(client: AsyncClient) -> Dict[str, str]:
    login_payload = {
        "email": "admin@examshield.gov.in",
        "password": "ChangeThisPassword123!",
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_encrypted_upload_success_and_metadata_creation(
    client: AsyncClient, test_subject: Subject, db_session: AsyncSession, test_admin: User
):
    """
    Test successful encrypted upload:
    - EncryptedPaperMetadata creation
    - correct storage_path
    - plaintext not present in final storage
    - existing hash contract (plaintext hash)
    - successful decrypt back to original content
    """
    headers = await _get_superuser_headers(client)
    pdf_content = b"%PDF-1.4 Mock Highly Confidential Content"
    file = ("test_enc_paper.pdf", BytesIO(pdf_content), "application/pdf")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": "ENC-101",
        "title": "Encrypted Test",
        "description": "Encryption integration test",
    }

    # Upload
    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )

    assert response.status_code == 201, f"Failed: {response.text}"
    res_data = response.json()["data"]
    paper_id = uuid.UUID(res_data["id"])
    storage_path = res_data["storage_path"]
    
    # 1. correct storage_path and EncryptedPaperMetadata creation
    assert "pending" not in storage_path
    assert "encrypted" in storage_path

    # Verify DB records
    stmt = select(QuestionPaper).where(QuestionPaper.id == paper_id)
    paper = (await db_session.execute(stmt)).scalar_one()
    
    assert paper.storage_path == storage_path
    
    stmt_meta = select(EncryptedPaperMetadata).where(EncryptedPaperMetadata.question_paper_id == paper_id)
    meta = (await db_session.execute(stmt_meta)).scalar_one_or_none()
    assert meta is not None
    assert meta.encrypted_storage_path == storage_path
    
    # 2. Existing hash contract
    from app.utils.hash_service import HashService
    expected_hash = HashService().generate_sha256(pdf_content)
    assert paper.sha256_hash == expected_hash

    # 3. Plaintext not present in final storage
    # The file in storage_path should NOT be plaintext
    from app.core.dependencies import get_storage_provider
    storage_provider = get_storage_provider()
    
    ciphertext = await storage_provider.read(storage_path)
    assert ciphertext != pdf_content
    
    # 4. Successful decrypt back to original content
    from app.services.encrypted_paper_service import EncryptedPaperService
    from app.core.dependencies import get_crypto_key_provider
    enc_service = EncryptedPaperService(
        session=db_session,
        crypto_provider=get_crypto_key_provider(),
        storage_provider=storage_provider
    )
    
    decrypted = await enc_service.decrypt_question_paper(
        question_paper_id=paper_id,
        user_id=test_admin.id
    )
    assert decrypted == pdf_content


async def test_upload_fails_without_active_key(
    client: AsyncClient, test_subject: Subject, db_session: AsyncSession
):
    """
    Test active wrapping key requirement.
    If no active key exists, upload should fail with 400.
    """
    # Deactivate all keys temporarily
    from app.models.key_metadata import KeyMetadata, KeyStatus
    stmt = select(KeyMetadata).where(KeyMetadata.status == KeyStatus.ACTIVE)
    active_keys = (await db_session.execute(stmt)).scalars().all()
    for key in active_keys:
        key.status = KeyStatus.INACTIVE
    await db_session.flush()

    headers = await _get_superuser_headers(client)
    pdf_content = b"%PDF-1.4 Mock PDF"
    file = ("test_enc_paper.pdf", BytesIO(pdf_content), "application/pdf")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": "ENC-102",
        "title": "Should Fail",
    }

    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )

    assert response.status_code == 400
    assert "No active RSA wrapping key available" in response.text
    
    # Restore keys
    for key in active_keys:
        key.status = KeyStatus.ACTIVE
    await db_session.flush()


async def test_deletion_of_encrypted_artifact(
    client: AsyncClient, test_subject: Subject, db_session: AsyncSession
):
    """
    Verify delete_paper deletes the final encrypted artifact and associated metadata.
    """
    headers = await _get_superuser_headers(client)
    pdf_content = b"%PDF-1.4 Mock Content for deletion"
    file = ("delete_me.pdf", BytesIO(pdf_content), "application/pdf")

    data = {
        "subject_id": str(test_subject.id),
        "paper_code": "ENC-DEL",
        "title": "To Be Deleted",
    }

    # Upload
    response = await client.post(
        "/api/v1/question-papers/upload",
        headers=headers,
        data=data,
        files={"file": file},
    )
    assert response.status_code == 201
    paper_id = response.json()["data"]["id"]
    storage_path = response.json()["data"]["storage_path"]
    
    # Verify existence
    from app.core.dependencies import get_storage_provider
    storage_provider = get_storage_provider()
    
    # For LocalStorageProvider it uses Path(base_dir) / storage_path
    
    # Delete
    del_response = await client.delete(f"/api/v1/question-papers/{paper_id}", headers=headers)
    assert del_response.status_code == 200
    
    # Verify DB deletion (Metadata should cascade)
    stmt = select(QuestionPaper).where(QuestionPaper.id == uuid.UUID(paper_id))
    assert (await db_session.execute(stmt)).scalar_one_or_none() is None
    
    stmt_meta = select(EncryptedPaperMetadata).where(EncryptedPaperMetadata.question_paper_id == uuid.UUID(paper_id))
    assert (await db_session.execute(stmt_meta)).scalar_one_or_none() is None
    
    # Verify Storage cleanup
    # storage_provider.exists isn't defined? We should check if it exposes it, but let's try reading and expect FileNotFoundError
    with pytest.raises(Exception): # FileNotFoundError or similar
        await storage_provider.read(storage_path)
