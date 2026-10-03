"""Stable application errors for object-storage operations."""

from enact.platform.errors import EnactError


class ObjectStorageError(EnactError):
    """Base error raised by the object-storage boundary."""


class ObjectNotFoundError(ObjectStorageError):
    """Raised when a requested object does not exist."""

    def __init__(self, key: str) -> None:
        """Initialize a missing-object error.

        Args:
            key: Storage key that could not be found.
        """
        super().__init__(
            message=f'Object {key!r} does not exist.',
            code='object_not_found',
        )


class ObjectStorageUnavailableError(ObjectStorageError):
    """Raised when the configured object store cannot complete an operation."""

    def __init__(self) -> None:
        """Initialize an unavailable-storage error."""
        super().__init__(
            message='Object storage is unavailable.',
            code='object_storage_unavailable',
        )
