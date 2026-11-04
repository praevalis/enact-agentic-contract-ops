"""Allow account-only sessions and add single-use organization invitations."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from enact.infrastructure.database.migrations import disable_tenant_rls, enable_tenant_rls
from sqlalchemy.dialects import postgresql

revision: str = '0005_organization_onboarding'
down_revision: str | None = '0004_drop_session_last_used'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'
TABLE = 'organization_invitations'


def upgrade() -> None:
    """Permit organization-free sessions and create tenant-scoped invitations."""
    op.alter_column('auth_sessions', 'current_organization_id', nullable=True, schema=SCHEMA)

    op.create_table(
        TABLE,
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('code_digest', sa.String(length=64), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('redeemed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('redeemed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'],
            [f'{SCHEMA}.organizations.id'],
            name='fk_organization_invitation_organization',
        ),
        sa.ForeignKeyConstraint(
            ['created_by_user_id'],
            [f'{SCHEMA}.users.id'],
            name='fk_organization_invitation_creator',
        ),
        sa.ForeignKeyConstraint(
            ['redeemed_by_user_id'],
            [f'{SCHEMA}.users.id'],
            name='fk_organization_invitation_redeemer',
        ),
        sa.UniqueConstraint('code_digest', name='uq_organization_invitation_code_digest'),
        sa.CheckConstraint(
            "role IN ('deal_desk', 'administrator', 'operations_reviewer', 'auditor')",
            name='organization_invitation_role',
        ),
        sa.CheckConstraint('expires_at > created_at', name='organization_invitation_expiry'),
        sa.CheckConstraint(
            '(redeemed_by_user_id IS NULL) = (redeemed_at IS NULL)',
            name='organization_invitation_redemption_pair',
        ),
        sa.Index('ix_organization_invitation_organization', 'organization_id', 'created_at'),
        schema=SCHEMA,
    )
    enable_tenant_rls(op, TABLE)

    # A bearer code may reveal only its matching row before organization context exists.
    op.execute(
        f'CREATE POLICY invitation_code_lookup ON {SCHEMA}.{TABLE} '
        'FOR SELECT TO enact_app USING ('
        "code_digest = NULLIF(current_setting('enact.invitation_digest', true), '')"
        ')'
    )
    op.execute(
        f'CREATE POLICY invitation_code_redeem ON {SCHEMA}.{TABLE} '
        'FOR UPDATE TO enact_app '
        "USING (code_digest = NULLIF(current_setting('enact.invitation_digest', true), '')) "
        "WITH CHECK (code_digest = NULLIF(current_setting('enact.invitation_digest', true), ''))"
    )
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA}.{TABLE} TO enact_app')


def downgrade() -> None:
    """Remove invitations and restore organization-required sessions."""
    op.execute(f'REVOKE ALL PRIVILEGES ON {SCHEMA}.{TABLE} FROM enact_app')
    op.execute(f'DROP POLICY invitation_code_redeem ON {SCHEMA}.{TABLE}')
    op.execute(f'DROP POLICY invitation_code_lookup ON {SCHEMA}.{TABLE}')
    disable_tenant_rls(op, TABLE)
    op.drop_table(TABLE, schema=SCHEMA)

    # A downgraded schema cannot retain account-only sessions.
    op.execute(f'DELETE FROM {SCHEMA}.auth_sessions WHERE current_organization_id IS NULL')
    op.alter_column('auth_sessions', 'current_organization_id', nullable=False, schema=SCHEMA)
