"""Identity and organization tenancy models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base
from ..mixins import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from .customers import Customer


class Organization(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """An Enact tenant."""

    __tablename__ = 'organizations'
    __table_args__ = (
        CheckConstraint(
            "status IN ('active', 'suspended', 'archived')", name='organization_status'
        ),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='active')
    memberships: Mapped[list['Membership']] = relationship(back_populates='organization')
    customers: Mapped[list['Customer']] = relationship(back_populates='organization')


class User(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """A locally authenticated human identity."""

    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("status IN ('active', 'disabled')", name='user_status'),)

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='active')
    memberships: Mapped[list['Membership']] = relationship(back_populates='user')


class Membership(UUIDPrimaryKeyMixin, CreatedAtMixin, UpdatedAtMixin, Base):
    """A user's role and status within one organization."""

    __tablename__ = 'memberships'
    __table_args__ = (
        UniqueConstraint('organization_id', 'id', name='uq_membership_organization_id_id'),
        UniqueConstraint('organization_id', 'user_id', name='uq_membership_organization_user'),
        CheckConstraint(
            "role IN ('deal_desk', 'administrator', 'operations_reviewer', 'auditor')",
            name='membership_role',
        ),
        CheckConstraint("status IN ('active', 'suspended', 'revoked')", name='membership_status'),
        Index('ix_membership_organization_user', 'organization_id', 'user_id'),
    )

    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    role: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default='active')
    organization: Mapped[Organization] = relationship(back_populates='memberships')
    user: Mapped[User] = relationship(back_populates='memberships')
