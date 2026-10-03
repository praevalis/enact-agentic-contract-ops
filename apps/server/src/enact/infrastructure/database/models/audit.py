"""Audit trail models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from ..base import Base
from ..mixins import UUIDPrimaryKeyMixin


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    """An append-only record of an actor's action on a tenant resource."""

    __tablename__ = 'audit_events'
    __table_args__ = (
        Index('ix_audit_event_organization_occurred', 'organization_id', 'occurred_at'),
        Index('ix_audit_event_resource', 'organization_id', 'resource_type', 'resource_id'),
    )

    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    actor_user_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('users.id')
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PostgresUUID(as_uuid=True))
    request_id: Mapped[str | None] = mapped_column(String(100))
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    details: Mapped[dict[str, object] | None] = mapped_column(JSON)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
