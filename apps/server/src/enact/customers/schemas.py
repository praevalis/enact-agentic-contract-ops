"""Public customer creation and read contracts."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from enact.platform.schemas import BaseRead, BaseWrite


class CustomerCreate(BaseWrite):
    """Customer display details to create within an organization."""

    display_name: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
    ]


class CustomerRead(BaseRead):
    """Customer identity and lifecycle state."""

    id: UUID
    organization_id: UUID
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime


class CustomerListRead(BaseRead):
    """A cursor page of customers visible to the active organization."""

    items: list[CustomerRead]
    next_cursor: str | None


class CustomerListParams(BaseWrite):
    """Pagination and filters for a tenant customer list."""

    page_size: int = Field(default=25, ge=1, le=100)
    cursor: str | None = None
    status: Literal['active', 'archived'] | None = None
    name_query: Annotated[
        str | None, StringConstraints(strip_whitespace=True, min_length=1, max_length=250)
    ] = None
