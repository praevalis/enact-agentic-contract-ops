"""Persistence-independent customer entity."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Customer:
    """An organization-owned contractual counterparty."""

    id: UUID
    organization_id: UUID
    display_name: str
    status: str
    created_at: datetime
    updated_at: datetime
