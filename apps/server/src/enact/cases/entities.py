"""Persistence-independent customer and case records."""

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
