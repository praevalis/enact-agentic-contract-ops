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


@dataclass(frozen=True, slots=True)
class CustomerCursor:
    """Position in the newest-first customer ordering."""

    id: UUID
    created_at: datetime


@dataclass(slots=True)
class CustomerPage:
    """A bounded customer collection and its next position."""

    items: list[Customer]
    next_cursor: CustomerCursor | None
