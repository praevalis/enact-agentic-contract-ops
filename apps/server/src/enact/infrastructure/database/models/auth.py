"""Authentication persistence models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.orm import Mapped, mapped_column

from ..base import Base
from ..mixins import CreatedAtMixin, UpdatedAtMixin, UUIDPrimaryKeyMixin


class AuthSession(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    """A revocable authentication session and refresh-token family member."""

    __tablename__ = 'auth_sessions'
    __table_args__ = (
        UniqueConstraint('refresh_token_digest', name='uq_auth_session_refresh_digest'),
        CheckConstraint('expires_at > created_at', name='auth_session_expiry_after_creation'),
        CheckConstraint(
            'revoked_at IS NULL OR revoked_at >= created_at',
            name='auth_session_revoked_after_creation',
        ),
        Index('ix_auth_session_user_active', 'user_id', 'revoked_at', 'expires_at'),
        Index('ix_auth_session_token_family', 'token_family_id'),
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('users.id'), nullable=False
    )
    current_organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('organizations.id'), nullable=False
    )
    token_family_id: Mapped[UUID] = mapped_column(PostgresUUID(as_uuid=True), nullable=False)
    refresh_token_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_session_id: Mapped[UUID | None] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('auth_sessions.id')
    )


class UserOrganizationPreference(CreatedAtMixin, UpdatedAtMixin, Base):
    """A user's persisted organization preference and recent-use state."""

    __tablename__ = 'user_organization_preferences'
    __table_args__ = (
        Index('ix_user_organization_preference_user_recent', 'user_id', 'last_used_at'),
    )

    user_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('users.id'), primary_key=True
    )
    organization_id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True), ForeignKey('organizations.id'), primary_key=True
    )
    is_preferred: Mapped[bool] = mapped_column(nullable=False, default=False)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
