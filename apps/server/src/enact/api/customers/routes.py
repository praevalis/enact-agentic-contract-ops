"""Customer creation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from enact.customers import (
    CustomerCreate,
    CustomerCursor,
    CustomerListParams,
    CustomerListRead,
    CustomerRead,
    CustomerService,
)
from enact.identity import Principal

from ..identity.dependencies import get_principal
from ..pagination import decode_cursor, encode_cursor
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


@router.get('', response_model=CustomerListRead)
async def list_customers(
    principal: Annotated[Principal, Depends(get_principal)],
    customers: Annotated[CustomerService, Depends(get_customer_service)],
    params: Annotated[CustomerListParams, Query()],
) -> CustomerListRead:
    """List customers visible to the active organization.

    Args:
        principal: Freshly validated organization principal.
        customers: Customer service for the request.
        params: Pagination and optional filters from the query string.

    Returns:
        Customers and an optional cursor for the next page.

    Raises:
        HTTPException: If the supplied cursor is malformed.
    """
    try:
        if params.cursor is not None:
            created_at, identifier = decode_cursor(params.cursor)
            position = CustomerCursor(id=identifier, created_at=created_at)
        else:
            position = None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    page = await customers.list(
        principal=principal,
        page_size=params.page_size,
        cursor=position,
        status=params.status,
        name_query=params.name_query,
    )
    return CustomerListRead(
        items=[CustomerRead.model_validate(item) for item in page.items],
        next_cursor=(
            encode_cursor(page.next_cursor.created_at, page.next_cursor.id)
            if page.next_cursor is not None
            else None
        ),
    )
