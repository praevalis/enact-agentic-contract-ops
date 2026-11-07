"""Case workflow models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .customers import Customer


class Case(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """A durable activation or amendment unit of work."""

    __tablename__ = 'cases'
    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'customer_id'], ['customers.organization_id', 'customers.id']
        ),
        UniqueConstraint('organization_id', 'id', name='uq_case_organization_id_id'),
        CheckConstraint("case_type IN ('activation', 'amendment')", name='case_type'),
        CheckConstraint(
            (
                "status IN ('draft', 'processing', 'blocked', 'ready', "
                "'completed', 'failed', 'cancelled')"
            ),
            name='case_status',
        ),
        CheckConstraint('concurrency_version > 0', name='case_concurrency_version'),
        Index('ix_case_organization_status', 'organization_id', 'status'),
    )

    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    case_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='draft')
    concurrency_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    customer: Mapped['Customer'] = relationship(back_populates='cases')


class CaseLineage(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A typed relationship between two cases in one organization."""

    __tablename__ = 'case_lineage'
    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'source_case_id'], ['cases.organization_id', 'cases.id']
        ),
        ForeignKeyConstraint(
            ['organization_id', 'target_case_id'], ['cases.organization_id', 'cases.id']
        ),
        UniqueConstraint(
            'organization_id',
            'source_case_id',
            'target_case_id',
            'relationship_type',
            name='uq_case_lineage_edge',
        ),
        CheckConstraint('source_case_id <> target_case_id', name='case_lineage_distinct_cases'),
        CheckConstraint(
            "relationship_type IN ('amends', 'supersedes', 'related_to')",
            name='case_lineage_relationship_type',
        ),
        Index('ix_case_lineage_source', 'organization_id', 'source_case_id'),
        Index('ix_case_lineage_target', 'organization_id', 'target_case_id'),
        Index(
            'uq_case_lineage_amends_target',
            'organization_id',
            'target_case_id',
            unique=True,
            postgresql_where=text("relationship_type = 'amends'"),
        ),
    )

    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    source_case_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    target_case_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    relationship_type: Mapped[str] = mapped_column(String(32), nullable=False)
    authority_metadata: Mapped[dict[str, object] | None] = mapped_column(JSON)
