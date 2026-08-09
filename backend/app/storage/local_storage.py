"""
ExamShield - Local File Storage Provider

Implements StorageInterface using the local filesystem.
Files are stored under a configurable base directory.
"""

import logging
import os
from pathlib import Path

import aiofiles

from app.storage.storage_interface import StorageInterface

logger = logging.getLogger("examshield.storage.local")


class LocalStorageProvider(StorageInterface):
    """
    Local filesystem storage provider.

    Stores files under a configurable base directory. Automatically
    creates parent directories as needed.
    """

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
        logger.info("LocalStorageProvider initialized at: %s", self._base_dir.resolve())

    def _resolve_path(self, relative_path: str) -> Path:
        """Resolve a relative path against the storage base directory."""
        return self._base_dir / relative_path

    async def save(self, file_data: bytes, destination_path: str) -> str:
        """
        Store file data on the local filesystem.

        Args:
            file_data: Raw bytes of the file to store.
            destination_path: Relative path within the base directory.

        Returns:
            The absolute storage path where the file was saved.
        """
        full_path = self._resolve_path(destination_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file_data)

        logger.info("File saved: %s (%d bytes)", full_path, len(file_data))
        return str(full_path)

    async def read(self, storage_path: str) -> bytes:
        """
        Read file contents from the local filesystem.

        Args:
            storage_path: The absolute path of the stored file.

        Returns:
            Raw bytes of the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        path = Path(storage_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {storage_path}")

        async with aiofiles.open(path, "rb") as f:
            data = await f.read()

        return data

    async def delete(self, storage_path: str) -> bool:
        """
        Delete a file from the local filesystem.

        Args:
            storage_path: The absolute path of the file to delete.

        Returns:
            True if the file was deleted, False if it did not exist.
        """
        path = Path(storage_path)
        if path.exists():
            path.unlink()
            logger.info("File deleted: %s", storage_path)
            return True
        return False

    async def exists(self, storage_path: str) -> bool:
        """
        Check whether a file exists on the local filesystem.

        Args:
            storage_path: The absolute path to check.

        Returns:
            True if the file exists, False otherwise.
        """
        return Path(storage_path).exists()
