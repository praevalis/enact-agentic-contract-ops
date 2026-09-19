"""Liveness and readiness endpoints."""

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from enact.platform.database.dependencies import get_database_manager
from enact.platform.database.manager import DatabaseManager
from enact.platform.object_storage import ObjectStorageManager, ObjectStorageUnavailableError
from enact.platform.object_storage.dependencies import get_object_storage_manager

router = APIRouter(prefix='/health', tags=['health'])


class HealthRead(BaseModel):
    """Health status returned by operational probes."""

    status: Literal['ok']


@router.get('/live', response_model=HealthRead)
async def read_liveness() -> HealthRead:
    """Report whether the API process can serve requests.

    Returns:
        A successful process-health result.
    """
    return HealthRead(status='ok')


@router.get('/ready', response_model=HealthRead)
async def read_readiness(
    database_manager: Annotated[DatabaseManager, Depends(get_database_manager)],
    object_storage_manager: Annotated[ObjectStorageManager, Depends(get_object_storage_manager)],
) -> HealthRead:
    """Report whether required API dependencies are available.

    Args:
        database_manager: Initialized database manager resolved by FastAPI.
        object_storage_manager: Initialized object-storage manager resolved by FastAPI.

    Returns:
        A successful dependency-health result.

    Raises:
        HTTPException: If database infrastructure is unavailable.
    """
    try:
        await database_manager.ping()
        await object_storage_manager.ping()
    except (RuntimeError, SQLAlchemyError, ObjectStorageUnavailableError) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='A required dependency is unavailable.',
        ) from error

    return HealthRead(status='ok')
