"""Public case creation and read contracts."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Self
from uuid import UUID

from pydantic import Field, StringConstraints, model_validator

from enact.platform.schemas import BaseRead, BaseWrite


class CaseType(StrEnum):
    """Supported intake case kinds."""

    ACTIVATION = 'activation'
    AMENDMENT = 'amendment'


class CaseCreate(BaseWrite):
    """New activation or amendment for an existing customer."""

    customer_id: UUID
    title: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)]
    case_type: CaseType
    prior_case_id: UUID | None = None

    @model_validator(mode='after')
    def validate_prior_case(self) -> Self:
        """Require lineage exactly when creating an amendment.

        Returns:
            Validated request.

        Raises:
            ValueError: If the prior-case field contradicts the case type.
        """
        if self.case_type == CaseType.AMENDMENT and self.prior_case_id is None:
            raise ValueError('An amendment requires prior_case_id.')

        if self.case_type == CaseType.ACTIVATION and self.prior_case_id is not None:
            raise ValueError('An activation cannot have prior_case_id.')

        return self


class CaseRead(BaseRead):
    """Case state and optional amendment predecessor."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    title: str
    case_type: CaseType
    status: str
    concurrency_version: int
    prior_case_id: UUID | None
    created_at: datetime
    updated_at: datetime


class CaseListRead(BaseRead):
    """A cursor page of cases visible to the active organization."""

    items: list[CaseRead]
    next_cursor: str | None


class CaseListParams(BaseWrite):
    """Pagination and filters for a tenant case list."""

    page_size: int = Field(default=25, ge=1, le=100)
    cursor: str | None = None
    customer_id: UUID | None = None
    case_type: CaseType | None = None
    status: str | None = None
