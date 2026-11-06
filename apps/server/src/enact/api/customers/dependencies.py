"""FastAPI dependencies for customer operations."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from enact.customers import CustomerService
from enact.infrastructure.database.dependencies import get_session
from enact.infrastructure.database.uows.customers import SqlAlchemyCustomerUnitOfWork


def get_customer_service(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> CustomerService:
    """Build a customer service over the request transaction.

    Args:
        session: Request-scoped database session.

    Returns:
        Customer creation service.
    """
    return CustomerService(uow=SqlAlchemyCustomerUnitOfWork(session))
