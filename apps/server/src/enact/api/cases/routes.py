"""Case creation and read APIs."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from enact.cases import CaseCreate, CaseListParams, CaseListRead, CaseRead, CaseService
from enact.identity import Principal

from ..identity.dependencies import get_principal
from .dependencies import get_case_service
from .pagination import decode_case_cursor, encode_case_cursor

router = APIRouter(prefix='/cases', tags=['cases'])


@router.post('', response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    payload: CaseCreate,
    principal: Annotated[Principal, Depends(get_principal)],
    cases: Annotated[CaseService, Depends(get_case_service)],
) -> CaseRead:
    """Create a draft activation or amendment for an existing customer.

    Args:
        payload: Customer, title, type, and optional amendment predecessor.
        principal: Freshly validated account or organization principal.
        cases: Case creation service.

    Returns:
        Created draft case and predecessor identifier.
    """
    case = await cases.create(
        principal=principal,
        customer_id=payload.customer_id,
        title=payload.title,
        case_type=payload.case_type,
        prior_case_id=payload.prior_case_id,
    )
    return CaseRead.model_validate(case)


@router.get('', response_model=CaseListRead)
async def list_cases(
    principal: Annotated[Principal, Depends(get_principal)],
    cases: Annotated[CaseService, Depends(get_case_service)],
    params: Annotated[CaseListParams, Query()],
) -> CaseListRead:
    """List cases visible to the active organization.

    Args:
        principal: Freshly validated organization principal.
        cases: Case service for the request.
        params: Pagination and optional filters from the query string.

    Returns:
        Cases and an optional cursor for the next page.

    Raises:
        HTTPException: If the supplied cursor is malformed.
    """
    try:
        position = decode_case_cursor(params.cursor) if params.cursor is not None else None
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    page = await cases.list(
        principal=principal,
        page_size=params.page_size,
        cursor=position,
        customer_id=params.customer_id,
        case_type=params.case_type,
        status=params.status,
    )
    return CaseListRead(
        items=[CaseRead.model_validate(item) for item in page.items],
        next_cursor=encode_case_cursor(page.next_cursor) if page.next_cursor is not None else None,
    )


@router.get('/{case_id}', response_model=CaseRead)
async def get_case(
    case_id: UUID,
    principal: Annotated[Principal, Depends(get_principal)],
    cases: Annotated[CaseService, Depends(get_case_service)],
) -> CaseRead:
    """Return one case and its amendment predecessor.

    Args:
        case_id: Case identifier.
        principal: Freshly validated organization principal.
        cases: Case service for the request.

    Returns:
        The visible case.
    """
    case = await cases.get(principal=principal, case_id=case_id)
    return CaseRead.model_validate(case)
