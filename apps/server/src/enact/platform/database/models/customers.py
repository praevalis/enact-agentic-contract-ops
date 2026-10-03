"""Customer registry models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import CheckConstraint, ForeignKeyConstraint, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .cases import Case
    from .identity import Organization


class Customer(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """A contractual counterparty owned by an organization."""

    __tablename__ = 'customers'
    __table_args__ = (
        ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        UniqueConstraint('organization_id', 'id', name='uq_customer_organization_id_id'),
        CheckConstraint("status IN ('active', 'archived')", name='customer_status'),
        Index('ix_customer_organization_name', 'organization_id', 'display_name'),
    )

    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    display_name: Mapped[str] = mapped_column(String(250), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='active')
    organization: Mapped['Organization'] = relationship(back_populates='customers')
    identifiers: Mapped[list['CustomerIdentifier']] = relationship(
        back_populates='customer', cascade='all, delete-orphan'
    )
    cases: Mapped[list['Case']] = relationship(back_populates='customer')


class CustomerIdentifier(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """An opaque identifier for a customer in an external namespace."""

    __tablename__ = 'customer_identifiers'
    __table_args__ = (
        ForeignKeyConstraint(
            ['organization_id', 'customer_id'], ['customers.organization_id', 'customers.id']
        ),
        UniqueConstraint(
            'organization_id',
            'issuing_system',
            'identifier_type',
            'identifier_value',
            name='uq_customer_identifier_namespace',
        ),
        Index('ix_customer_identifier_customer', 'organization_id', 'customer_id'),
    )

    organization_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    customer_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    identifier_type: Mapped[str] = mapped_column(String(64), nullable=False)
    identifier_value: Mapped[str] = mapped_column(String(500), nullable=False)
    issuing_system: Mapped[str | None] = mapped_column(String(120))
    customer: Mapped[Customer] = relationship(back_populates='identifiers')
