"""
ExamShield - Encrypted Paper Service Tests

Tests the full encrypt/decrypt lifecycle using existing cryptographic
components (AES-256-GCM, RSA-OAEP via LocalCryptoKeyProvider),
StorageInterface, and EncryptedPaperMetadata persistence.
"""

import base64
import uuid
from datetime import date

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.encrypted_paper_metadata import EncryptedPaperMetadata
from app.models.exam import Exam, ExamStatus
from app.models.key_metadata import (
    Algorithm,
    KeyMetadata,
    KeyPurpose,
    KeyStatus,
)
from app.models.question_paper import QuestionPaper, QuestionPaperStatus
from app.models.subject import Subject, SubjectStatus
from app.models.user import User
from app.modules.security.providers.local_crypto_provider import (
    LocalCryptoKeyProvider,
)
from app.repositories.encrypted_paper_metadata_repository import (
    EncryptedPaperMetadataRepository,
)
from app.services.encrypted_paper_service import EncryptedPaperService
from app.storage.storage_interface import StorageInterface

pytestmark = pytest.mark.asyncio


# ── In-Memory Storage Fake ───────────────────────────────────────
class InMemoryStorageProvider(StorageInterface):
    """Minimal in-memory storage provider for testing."""

    def __init__(self) -> None:
        self._store: dict[str, bytes] = {}

    async def save(self, file_data: bytes, destination_path: str) -> str:
        self._store[destination_path] = file_data
        return destination_path

    async def read(self, storage_path: str) -> bytes:
        if storage_path not in self._store:
            raise FileNotFoundError(f"File not found: {storage_path}")
        return self._store[storage_path]

    async def delete(self, storage_path: str) -> bool:
        if storage_path in self._store:
            del self._store[storage_path]
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        return storage_path in self._store


# ── Fixtures ─────────────────────────────────────────────────────
@pytest_asyncio.fixture
async def crypto_provider(tmp_path) -> LocalCryptoKeyProvider:
    """Return a LocalCryptoKeyProvider with a pre-generated RSA key."""
    provider = LocalCryptoKeyProvider(key_dir=tmp_path)
    await provider.generate_rsa_key("test-rsa-key-v1")
    return provider


@pytest_asyncio.fixture
async def storage_provider() -> InMemoryStorageProvider:
    return InMemoryStorageProvider()


@pytest_asyncio.fixture
async def key_metadata_record(
    db_session: AsyncSession,
    test_admin: User,
) -> KeyMetadata:
    """Create a KeyMetadata record matching the crypto provider key."""
    km = KeyMetadata(
        key_identifier="test-rsa-key-v1",
        algorithm=Algorithm.RSA4096,
        key_purpose=KeyPurpose.WRAPPING,
        status=KeyStatus.ACTIVE,
        created_by=test_admin.id,
    )
    db_session.add(km)
    await db_session.flush()
    return km


@pytest_asyncio.fixture
async def enc_service(
    db_session: AsyncSession,
    crypto_provider: LocalCryptoKeyProvider,
    storage_provider: InMemoryStorageProvider,
) -> EncryptedPaperService:
    return EncryptedPaperService(
        session=db_session,
        crypto_provider=crypto_provider,
        storage_provider=storage_provider,
    )


PLAINTEXT = b"This is a highly confidential NEET question paper for Physics Section A."


# ── Test: Encrypt succeeds ───────────────────────────────────────
async def test_encrypt_paper_succeeds(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    assert result.question_paper_id == test_paper.id
    assert result.key_identifier == "test-rsa-key-v1"
    assert result.encryption_algorithm == "AES256_GCM"
    assert result.encryption_version == 1
    assert result.encrypted_storage_path != ""
    assert result.ciphertext_sha256 != ""


# ── Test: Encrypted output differs from plaintext ────────────────
async def test_encrypted_output_differs_from_plaintext(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    stored_data = await storage_provider.read(result.encrypted_storage_path)
    assert stored_data != PLAINTEXT


# ── Test: Decrypt returns original plaintext ─────────────────────
async def test_decrypt_returns_original_plaintext(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    decrypted = await enc_service.decrypt_question_paper(
        question_paper_id=test_paper.id,
        user_id=test_admin.id,
    )

    assert decrypted == PLAINTEXT


# ── Test: Every encryption gets a different nonce ────────────────
async def test_every_encryption_gets_different_nonce(
    db_session: AsyncSession,
    test_admin: User,
    test_subject: Subject,
    key_metadata_record: KeyMetadata,
    crypto_provider: LocalCryptoKeyProvider,
    storage_provider: InMemoryStorageProvider,
):
    """Each encryption must produce a different nonce."""
    paper1 = QuestionPaper(
        subject_id=test_subject.id,
        paper_code="NONCE-A",
        title="Nonce Test A",
        version=1,
        status=QuestionPaperStatus.UPLOADED,
        file_name="a.pdf",
        original_file_name="a.pdf",
        storage_path="path/a.pdf",
        mime_type="application/pdf",
        file_size=100,
        sha256_hash="aaa",
        uploaded_by=test_admin.id,
    )
    paper2 = QuestionPaper(
        subject_id=test_subject.id,
        paper_code="NONCE-B",
        title="Nonce Test B",
        version=1,
        status=QuestionPaperStatus.UPLOADED,
        file_name="b.pdf",
        original_file_name="b.pdf",
        storage_path="path/b.pdf",
        mime_type="application/pdf",
        file_size=100,
        sha256_hash="bbb",
        uploaded_by=test_admin.id,
    )
    db_session.add_all([paper1, paper2])
    await db_session.flush()

    svc = EncryptedPaperService(
        session=db_session,
        crypto_provider=crypto_provider,
        storage_provider=storage_provider,
    )

    await svc.encrypt_question_paper(
        question_paper_id=paper1.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await svc.encrypt_question_paper(
        question_paper_id=paper2.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    repo = EncryptedPaperMetadataRepository(db_session)
    m1 = await repo.get_by_question_paper_id(paper1.id)
    m2 = await repo.get_by_question_paper_id(paper2.id)

    assert m1.nonce != m2.nonce


# ── Test: Every encryption gets a different wrapped AES key ──────
async def test_every_encryption_gets_different_wrapped_key(
    db_session: AsyncSession,
    test_admin: User,
    test_subject: Subject,
    key_metadata_record: KeyMetadata,
    crypto_provider: LocalCryptoKeyProvider,
    storage_provider: InMemoryStorageProvider,
):
    paper1 = QuestionPaper(
        subject_id=test_subject.id,
        paper_code="KEY-A",
        title="Key Test A",
        version=1,
        status=QuestionPaperStatus.UPLOADED,
        file_name="ka.pdf",
        original_file_name="ka.pdf",
        storage_path="path/ka.pdf",
        mime_type="application/pdf",
        file_size=100,
        sha256_hash="ka",
        uploaded_by=test_admin.id,
    )
    paper2 = QuestionPaper(
        subject_id=test_subject.id,
        paper_code="KEY-B",
        title="Key Test B",
        version=1,
        status=QuestionPaperStatus.UPLOADED,
        file_name="kb.pdf",
        original_file_name="kb.pdf",
        storage_path="path/kb.pdf",
        mime_type="application/pdf",
        file_size=100,
        sha256_hash="kb",
        uploaded_by=test_admin.id,
    )
    db_session.add_all([paper1, paper2])
    await db_session.flush()

    svc = EncryptedPaperService(
        session=db_session,
        crypto_provider=crypto_provider,
        storage_provider=storage_provider,
    )

    await svc.encrypt_question_paper(
        question_paper_id=paper1.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await svc.encrypt_question_paper(
        question_paper_id=paper2.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    repo = EncryptedPaperMetadataRepository(db_session)
    m1 = await repo.get_by_question_paper_id(paper1.id)
    m2 = await repo.get_by_question_paper_id(paper2.id)

    assert m1.wrapped_key != m2.wrapped_key


# ── Test: Tampered ciphertext fails authentication ───────────────
async def test_tampered_ciphertext_fails(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    # Tamper with stored ciphertext
    ciphertext = await storage_provider.read(result.encrypted_storage_path)
    tampered = bytearray(ciphertext)
    tampered[0] ^= 0xFF
    await storage_provider.save(bytes(tampered), result.encrypted_storage_path)

    from app.exceptions.api_exception import BadRequestException

    with pytest.raises(BadRequestException, match="authentication failed"):
        await enc_service.decrypt_question_paper(
            question_paper_id=test_paper.id,
            user_id=test_admin.id,
        )


# ── Test: Tampered nonce fails authentication ────────────────────
async def test_tampered_nonce_fails(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    # Tamper with the stored nonce
    repo = EncryptedPaperMetadataRepository(db_session)
    metadata = await repo.get_by_question_paper_id(test_paper.id)
    original_nonce_bytes = base64.b64decode(metadata.nonce)
    tampered_nonce = bytearray(original_nonce_bytes)
    tampered_nonce[0] ^= 0xFF
    metadata.nonce = base64.b64encode(bytes(tampered_nonce)).decode("ascii")
    await db_session.flush()

    from app.exceptions.api_exception import BadRequestException

    with pytest.raises(BadRequestException, match="authentication failed"):
        await enc_service.decrypt_question_paper(
            question_paper_id=test_paper.id,
            user_id=test_admin.id,
        )


# ── Test: Tampered wrapped AES key fails ─────────────────────────
async def test_tampered_wrapped_key_fails(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    # Tamper with the wrapped key
    repo = EncryptedPaperMetadataRepository(db_session)
    metadata = await repo.get_by_question_paper_id(test_paper.id)
    wrapped_bytes = base64.b64decode(metadata.wrapped_key)
    tampered_wrapped = bytearray(wrapped_bytes)
    tampered_wrapped[0] ^= 0xFF
    metadata.wrapped_key = base64.b64encode(bytes(tampered_wrapped)).decode("ascii")
    await db_session.flush()

    from app.exceptions.api_exception import BadRequestException

    with pytest.raises(BadRequestException):
        await enc_service.decrypt_question_paper(
            question_paper_id=test_paper.id,
            user_id=test_admin.id,
        )


# ── Test: Wrong RSA key fails ────────────────────────────────────
async def test_wrong_rsa_key_fails(
    db_session: AsyncSession,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
    tmp_path,
):
    """Encrypting with one RSA key and decrypting with another must fail."""
    crypto1 = LocalCryptoKeyProvider(key_dir=tmp_path / "crypto1")
    await crypto1.generate_rsa_key("test-rsa-key-v1")

    svc_encrypt = EncryptedPaperService(
        session=db_session,
        crypto_provider=crypto1,
        storage_provider=storage_provider,
    )

    await svc_encrypt.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    # Decrypt with a different crypto provider (different RSA key pair)
    crypto2 = LocalCryptoKeyProvider(key_dir=tmp_path / "crypto2")
    await crypto2.generate_rsa_key("test-rsa-key-v1")  # same name, different key

    svc_decrypt = EncryptedPaperService(
        session=db_session,
        crypto_provider=crypto2,
        storage_provider=storage_provider,
    )

    from app.exceptions.api_exception import BadRequestException

    with pytest.raises(BadRequestException):
        await svc_decrypt.decrypt_question_paper(
            question_paper_id=test_paper.id,
            user_id=test_admin.id,
        )


# ── Test: Metadata created correctly ─────────────────────────────
async def test_metadata_created_correctly(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    repo = EncryptedPaperMetadataRepository(db_session)
    metadata = await repo.get_by_question_paper_id(test_paper.id)

    assert metadata is not None
    assert metadata.question_paper_id == test_paper.id
    assert metadata.key_identifier == "test-rsa-key-v1"
    assert metadata.encryption_algorithm == "AES256_GCM"
    assert metadata.encryption_version == 1
    assert metadata.nonce != ""
    assert metadata.wrapped_key != ""
    assert metadata.encrypted_storage_path != ""


# ── Test: Plaintext AES key is NOT persisted ─────────────────────
async def test_plaintext_aes_key_not_persisted(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    repo = EncryptedPaperMetadataRepository(db_session)
    metadata = await repo.get_by_question_paper_id(test_paper.id)

    # The wrapped_key is Base64-encoded RSA-wrapped bytes, not a 32-byte AES key
    wrapped_raw = base64.b64decode(metadata.wrapped_key)
    # RSA-4096 wrapped output is 512 bytes, AES-256 key is 32 bytes
    assert len(wrapped_raw) == 512
    assert len(wrapped_raw) != 32  # not a plaintext AES key


# ── Test: RSA private key is NOT in metadata ─────────────────────
async def test_rsa_private_key_not_in_metadata(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
):
    await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    repo = EncryptedPaperMetadataRepository(db_session)
    metadata = await repo.get_by_question_paper_id(test_paper.id)

    # Verify no column contains RSA private key markers
    all_fields = (
        metadata.nonce
        + metadata.wrapped_key
        + metadata.encrypted_storage_path
        + metadata.key_identifier
        + metadata.encryption_algorithm
    )
    assert "BEGIN RSA PRIVATE KEY" not in all_fields
    assert "BEGIN PRIVATE KEY" not in all_fields


# ── Test: Encrypted artifact stored via storage provider ─────────
async def test_encrypted_artifact_stored(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    assert await storage_provider.exists(result.encrypted_storage_path)
    stored = await storage_provider.read(result.encrypted_storage_path)
    assert len(stored) > 0


# ── Test: Missing metadata produces NotFoundException ────────────
async def test_decrypt_missing_metadata_raises(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
):
    from app.exceptions.api_exception import NotFoundException

    with pytest.raises(NotFoundException, match="No encryption metadata"):
        await enc_service.decrypt_question_paper(
            question_paper_id=uuid.uuid4(),
            user_id=test_admin.id,
        )


# ── Test: Missing artifact produces NotFoundException ────────────
async def test_decrypt_missing_artifact_raises(
    db_session: AsyncSession,
    enc_service: EncryptedPaperService,
    test_admin: User,
    test_paper: QuestionPaper,
    key_metadata_record: KeyMetadata,
    storage_provider: InMemoryStorageProvider,
):
    result = await enc_service.encrypt_question_paper(
        question_paper_id=test_paper.id,
        plaintext_content=PLAINTEXT,
        key_identifier="test-rsa-key-v1",
        user_id=test_admin.id,
    )
    await db_session.flush()

    # Delete the artifact from storage
    await storage_provider.delete(result.encrypted_storage_path)

    from app.exceptions.api_exception import NotFoundException

    with pytest.raises(NotFoundException, match="Encrypted artifact not found"):
        await enc_service.decrypt_question_paper(
            question_paper_id=test_paper.id,
            user_id=test_admin.id,
        )
