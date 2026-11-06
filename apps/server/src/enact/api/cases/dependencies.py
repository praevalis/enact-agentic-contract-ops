"""FastAPI dependencies for case operations."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from enact.cases import CaseService
from enact.infrastructure.database.dependencies import get_session
from enact.infrastructure.database.uows.cases import SqlAlchemyCaseUnitOfWork


def get_case_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CaseService:
    """Build a case service over the request transaction.

    Args:
        session: Request-scoped database session.

    Returns:
        Case creation service.
    """
    return CaseService(uow=SqlAlchemyCaseUnitOfWork(session))
