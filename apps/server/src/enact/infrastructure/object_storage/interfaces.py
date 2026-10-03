"""Application-facing object-storage contract and values."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    """Metadata describing one stored object."""

    key: str
    content_length: int
    content_type: str | None
    etag: str | None
    metadata: Mapping[str, str]


@dataclass(frozen=True, slots=True)
class StoredObject:
    """A stored object's bytes and metadata."""

    content: bytes
    details: ObjectMetadata


class ObjectStorage(Protocol):
    """Store and retrieve opaque application-owned objects."""

    async def put_object(
        self,
        key: str,
        content: bytes,
        content_type: str,
        metadata: Mapping[str, str] | None = None,
    ) -> ObjectMetadata:
        """Store bytes at an application-owned key.

        Args:
            key: Opaque storage key selected by the calling application service.
            content: Complete object content.
            content_type: Media type recorded with the object.
            metadata: Optional application metadata recorded with the object.

        Returns:
            Metadata describing the stored object.

        Raises:
            ObjectStorageUnavailableError: If the object cannot be stored.
        """
        ...

    async def get_object(self, key: str) -> StoredObject:
        """Retrieve an object's bytes and metadata.

        Args:
            key: Opaque storage key.

        Returns:
            The stored bytes and their metadata.

        Raises:
            ObjectNotFoundError: If the key does not exist.
            ObjectStorageUnavailableError: If the object cannot be retrieved.
        """
        ...

    async def stat_object(self, key: str) -> ObjectMetadata:
        """Retrieve metadata without downloading object content.

        Args:
            key: Opaque storage key.

        Returns:
            Metadata describing the stored object.

        Raises:
            ObjectNotFoundError: If the key does not exist.
            ObjectStorageUnavailableError: If metadata cannot be retrieved.
        """
        ...

    async def delete_object(self, key: str) -> None:
        """Delete an object if it exists.

        Args:
            key: Opaque storage key.

        Raises:
            ObjectStorageUnavailableError: If the delete cannot be completed.
        """
        ...

    async def ping(self) -> None:
        """Verify that the configured bucket is accessible.

        Raises:
            ObjectStorageUnavailableError: If the bucket cannot be accessed.
        """
        ...
