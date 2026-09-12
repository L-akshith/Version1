import os
from pathlib import Path

import pytest

from app.core.config import Settings
from app.storage.local_storage import LocalStorageProvider


@pytest.mark.asyncio
async def test_local_storage_provider_custom_dir(tmp_path):
    """Verify LocalStorageProvider initializes at custom base_dir (e.g. /app/data/uploads)."""
    custom_dir = tmp_path / "app" / "data" / "uploads"
    provider = LocalStorageProvider(base_dir=custom_dir)
    assert provider._base_dir == custom_dir.resolve()
    assert custom_dir.exists()

    # Save and read test file
    saved_path = await provider.save(b"test file data", "question_papers/paper1.pdf")
    assert str(custom_dir.resolve()) in saved_path
    assert await provider.exists(saved_path) is True

    read_data = await provider.read(saved_path)
    assert read_data == b"test file data"

    assert await provider.delete(saved_path) is True
    assert await provider.exists(saved_path) is False


@pytest.mark.asyncio
async def test_local_storage_provider_env_var(tmp_path, monkeypatch):
    """Verify LocalStorageProvider resolves UPLOAD_DIR environment variable."""
    env_dir = tmp_path / "app" / "data" / "uploads_env"
    monkeypatch.setenv("UPLOAD_DIR", str(env_dir))

    provider = LocalStorageProvider()
    assert provider._base_dir == env_dir.resolve()
    assert env_dir.exists()


@pytest.mark.asyncio
async def test_settings_upload_dir_and_local_keys_dir(monkeypatch):
    """Verify Settings picks up UPLOAD_DIR and LOCAL_KEYS_DIR env vars properly."""
    monkeypatch.setenv("UPLOAD_DIR", "/app/data/uploads")
    monkeypatch.setenv("LOCAL_KEYS_DIR", "/app/data/.local_keys")

    settings = Settings()
    assert settings.UPLOAD_DIR == "/app/data/uploads"
    assert settings.LOCAL_KEYS_DIR == "/app/data/.local_keys"
