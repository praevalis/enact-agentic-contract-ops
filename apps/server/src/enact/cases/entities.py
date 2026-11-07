"""Persistence-independent case records and pagination values."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Case:
    """A durable activation or amendment case."""

    id: UUID
    organization_id: UUID
    customer_id: UUID
    title: str
    case_type: str
    status: str
    concurrency_version: int
    created_at: datetime
    updated_at: datetime
    prior_case_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class CaseCursor:
    """Position in the newest-first case ordering."""

    id: UUID
    created_at: datetime


@dataclass(slots=True)
class CasePage:
    """A bounded case collection and its next position."""

    items: list[Case]
    next_cursor: CaseCursor | None
