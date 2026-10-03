"""S3-compatible object-storage boundary and MinIO adapter."""

from .errors import ObjectNotFoundError, ObjectStorageError, ObjectStorageUnavailableError
from .interfaces import ObjectMetadata, ObjectStorage, StoredObject
from .manager import ObjectStorageManager

__all__ = [
    'ObjectMetadata',
    'ObjectNotFoundError',
    'ObjectStorage',
    'ObjectStorageError',
    'ObjectStorageManager',
    'ObjectStorageUnavailableError',
    'StoredObject',
]
