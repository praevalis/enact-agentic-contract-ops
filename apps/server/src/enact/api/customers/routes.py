"""Customer creation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from enact.customers import CustomerCreate, CustomerRead, CustomerService
from enact.identity import Principal

from ..identity.dependencies import get_principal
from .dependencies import get_customer_service

router = APIRouter(prefix='/customers', tags=['customers'])


@router.post('', response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    payload: CustomerCreate,
    principal: Annotated[Principal, Depends(get_principal)],
    customers: Annotated[CustomerService, Depends(get_customer_service)],
) -> CustomerRead:
    """Create a customer independently of case intake.

    Args:
        payload: Customer display name.
        principal: Freshly validated account or organization principal.
        customers: Customer creation service.

    Returns:
        Created customer.
    """
    customer = await customers.create(principal=principal, display_name=payload.display_name)
    return CustomerRead.model_validate(customer)
