"""
ExamShield - Storage Interface

Abstract base class defining the contract for all file storage providers.
Allows swapping between local filesystem, S3, Azure Blob, or MinIO
without modifying business logic.
"""

import abc
from typing import Optional


class StorageInterface(abc.ABC):
    """
    Abstract storage provider interface.

    All concrete storage implementations (local filesystem, S3,
    Azure Blob, MinIO) must implement these methods.
    """

    @abc.abstractmethod
    async def save(self, file_data: bytes, destination_path: str) -> str:
        """
        Store file data at the given destination path.

        Args:
            file_data: Raw bytes of the file to store.
            destination_path: Relative path within the storage root.

        Returns:
            The full storage path where the file was saved.
        """

    @abc.abstractmethod
    async def read(self, storage_path: str) -> bytes:
        """
        Read file contents from storage.

        Args:
            storage_path: The storage path returned by save().

        Returns:
            Raw bytes of the stored file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """

    @abc.abstractmethod
    async def delete(self, storage_path: str) -> bool:
        """
        Delete a file from storage.

        Args:
            storage_path: The storage path of the file to delete.

        Returns:
            True if the file was deleted, False if it did not exist.
        """

    @abc.abstractmethod
    async def exists(self, storage_path: str) -> bool:
        """
        Check whether a file exists at the given storage path.

        Args:
            storage_path: The storage path to check.

        Returns:
            True if the file exists, False otherwise.
        """
