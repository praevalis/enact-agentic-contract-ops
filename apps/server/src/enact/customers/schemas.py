"""Public customer creation and read contracts."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import StringConstraints

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
