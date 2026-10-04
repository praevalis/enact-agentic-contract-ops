"""Add authentication session and organization preference persistence."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '0002_auth_sessions'
down_revision: str | None = '0001_identity_case'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'
AUTH_TABLES = ('user_organization_preferences', 'auth_sessions')


def upgrade() -> None:
    """Create global authentication control-plane tables and grants.

    These tables are global control-plane data because authentication starts before an
    organization context is selected. They therefore do not use tenant RLS; application
    access remains restricted through the scoped runtime role and identity workflows.
    """
    op.create_table(
        'auth_sessions',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('current_organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('token_family_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('refresh_token_digest', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('replaced_by_session_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(['user_id'], [f'{SCHEMA}.users.id'], name='fk_auth_session_user'),
        sa.ForeignKeyConstraint(
            ['current_organization_id'],
            [f'{SCHEMA}.organizations.id'],
            name='fk_auth_session_current_organization',
        ),
        sa.ForeignKeyConstraint(
            ['replaced_by_session_id'],
            [f'{SCHEMA}.auth_sessions.id'],
            name='fk_auth_session_replacement',
        ),
        sa.UniqueConstraint('refresh_token_digest', name='uq_auth_session_refresh_digest'),
        sa.CheckConstraint('expires_at > created_at', name='auth_session_expiry_after_creation'),
        sa.CheckConstraint(
            'revoked_at IS NULL OR revoked_at >= created_at',
            name='auth_session_revoked_after_creation',
        ),
        sa.Index('ix_auth_session_user_active', 'user_id', 'revoked_at', 'expires_at'),
        sa.Index('ix_auth_session_token_family', 'token_family_id'),
        schema=SCHEMA,
    )
    op.create_table(
        'user_organization_preferences',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('is_preferred', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], [f'{SCHEMA}.users.id'], name='fk_user_organization_preference_user'
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'],
            [f'{SCHEMA}.organizations.id'],
            name='fk_user_organization_preference_organization',
        ),
        sa.Index(
            'ix_user_organization_preference_user_recent',
            'user_id',
            'last_used_at',
        ),
        schema=SCHEMA,
    )

    for table in reversed(AUTH_TABLES):
        op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA}.{table} TO enact_app')


def downgrade() -> None:
    """Remove authentication control-plane tables and runtime grants."""
    for table in AUTH_TABLES:
        op.execute(f'REVOKE ALL PRIVILEGES ON {SCHEMA}.{table} FROM enact_app')
        op.drop_table(table, schema=SCHEMA)
