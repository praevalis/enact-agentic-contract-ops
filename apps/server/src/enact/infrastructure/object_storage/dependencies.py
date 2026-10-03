"""FastAPI dependency adapters for object-storage infrastructure."""

from typing import Annotated, cast

from fastapi import Depends, Request

from .interfaces import ObjectStorage
from .manager import ObjectStorageManager


def get_object_storage_manager(request: Request) -> ObjectStorageManager:
    """Return the application object-storage manager.

    Args:
        request: Active request containing application infrastructure state.

    Returns:
        The process-wide object-storage manager.
    """
    return cast(ObjectStorageManager, request.app.state.object_storage_manager)


def get_object_storage(
    manager: Annotated[ObjectStorageManager, Depends(get_object_storage_manager)],
) -> ObjectStorage:
    """Return the initialized object-storage adapter.

    Args:
        manager: Object-storage manager resolved by FastAPI state.

    Returns:
        The process-wide object-storage adapter.

    Raises:
        RuntimeError: If object storage has not been initialized.
    """
    return manager.get_storage()
