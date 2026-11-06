"""Case creation API."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, status

from enact.cases import CaseCreate, CaseRead, CaseService
from enact.identity import Principal

from ..identity.dependencies import get_principal
from .dependencies import get_case_service

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
    return CaseRead.model_validate({**asdict(case), 'prior_case_id': payload.prior_case_id})
