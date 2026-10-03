"""Add identity, customer, case, and audit persistence."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from enact.infrastructure.database.migrations import disable_tenant_rls, enable_tenant_rls
from sqlalchemy.dialects import postgresql

revision: str = '0001_identity_case'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'
TENANT_TABLES = (
    'memberships',
    'customers',
    'customer_identifiers',
    'cases',
    'case_lineage',
    'audit_events',
)
ALL_TABLES = ('organizations', 'users', *TENANT_TABLES)


def upgrade() -> None:
    """Create identity, customer, case, and audit tables, grants, and tenant isolation."""
    op.execute('CREATE EXTENSION IF NOT EXISTS pgcrypto')

    op.create_table(
        'organizations',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'archived')", name='organization_status'
        ),
        schema=SCHEMA,
    )
    op.create_table(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.CheckConstraint("status IN ('active', 'disabled')", name='user_status'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        schema=SCHEMA,
    )
    op.create_table(
        'memberships',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'], [f'{SCHEMA}.organizations.id'], name='fk_membership_organization'
        ),
        sa.ForeignKeyConstraint(['user_id'], [f'{SCHEMA}.users.id'], name='fk_membership_user'),
        sa.UniqueConstraint('organization_id', 'id', name='uq_membership_organization_id_id'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_membership_organization_user'),
        sa.CheckConstraint(
            "role IN ('deal_desk', 'administrator', 'operations_reviewer', 'auditor')",
            name='membership_role',
        ),
        sa.CheckConstraint(
            "status IN ('active', 'suspended', 'revoked')", name='membership_status'
        ),
        sa.Index('ix_membership_organization_user', 'organization_id', 'user_id'),
        schema=SCHEMA,
    )
    op.create_table(
        'customers',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=250), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id'], [f'{SCHEMA}.organizations.id'], name='fk_customer_organization'
        ),
        sa.UniqueConstraint('organization_id', 'id', name='uq_customer_organization_id_id'),
        sa.CheckConstraint("status IN ('active', 'archived')", name='customer_status'),
        sa.Index('ix_customer_organization_name', 'organization_id', 'display_name'),
        schema=SCHEMA,
    )
    op.create_table(
        'customer_identifiers',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('identifier_type', sa.String(length=64), nullable=False),
        sa.Column('identifier_value', sa.String(length=500), nullable=False),
        sa.Column('issuing_system', sa.String(length=120), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id', 'customer_id'],
            [f'{SCHEMA}.customers.organization_id', f'{SCHEMA}.customers.id'],
            name='fk_customer_identifier_customer',
        ),
        sa.UniqueConstraint(
            'organization_id',
            'issuing_system',
            'identifier_type',
            'identifier_value',
            name='uq_customer_identifier_namespace',
        ),
        sa.Index('ix_customer_identifier_customer', 'organization_id', 'customer_id'),
        schema=SCHEMA,
    )
    op.create_table(
        'cases',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=250), nullable=False),
        sa.Column('case_type', sa.String(length=32), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='draft'),
        sa.Column('concurrency_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id', 'customer_id'],
            [f'{SCHEMA}.customers.organization_id', f'{SCHEMA}.customers.id'],
            name='fk_case_customer',
        ),
        sa.UniqueConstraint('organization_id', 'id', name='uq_case_organization_id_id'),
        sa.CheckConstraint("case_type IN ('activation', 'amendment')", name='case_type'),
        sa.CheckConstraint(
            (
                "status IN (''draft'', ''processing'', ''blocked'', ''ready'', "
                "''completed'', ''failed'', ''cancelled'')"
            ),
            name='case_status',
        ),
        sa.CheckConstraint('concurrency_version > 0', name='case_concurrency_version'),
        sa.Index('ix_case_organization_status', 'organization_id', 'status'),
        schema=SCHEMA,
    )
    op.create_table(
        'case_lineage',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('source_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('target_case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(length=32), nullable=False),
        sa.Column('authority_metadata', postgresql.JSONB(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['organization_id', 'source_case_id'],
            [f'{SCHEMA}.cases.organization_id', f'{SCHEMA}.cases.id'],
            name='fk_case_lineage_source',
        ),
        sa.ForeignKeyConstraint(
            ['organization_id', 'target_case_id'],
            [f'{SCHEMA}.cases.organization_id', f'{SCHEMA}.cases.id'],
            name='fk_case_lineage_target',
        ),
        sa.UniqueConstraint(
            'organization_id',
            'source_case_id',
            'target_case_id',
            'relationship_type',
            name='uq_case_lineage_edge',
        ),
        sa.CheckConstraint('source_case_id <> target_case_id', name='case_lineage_distinct_cases'),
        sa.CheckConstraint(
            "relationship_type IN ('amends', 'supersedes', 'related_to')",
            name='case_lineage_relationship_type',
        ),
        sa.Index('ix_case_lineage_source', 'organization_id', 'source_case_id'),
        sa.Index('ix_case_lineage_target', 'organization_id', 'target_case_id'),
        schema=SCHEMA,
    )
    op.create_table(
        'audit_events',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('actor_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=100), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request_id', sa.String(length=100), nullable=True),
        sa.Column('correlation_id', sa.String(length=100), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column(
            'occurred_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ['actor_user_id'], [f'{SCHEMA}.users.id'], name='fk_audit_event_actor'
        ),
        sa.Index('ix_audit_event_organization_occurred', 'organization_id', 'occurred_at'),
        sa.Index('ix_audit_event_resource', 'organization_id', 'resource_type', 'resource_id'),
        schema=SCHEMA,
    )

    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA}.organizations TO enact_app')
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA}.users TO enact_app')
    for table in TENANT_TABLES[:-1]:
        op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON {SCHEMA}.{table} TO enact_app')
    op.execute(f'GRANT SELECT, INSERT ON {SCHEMA}.audit_events TO enact_app')
    for table in TENANT_TABLES:
        enable_tenant_rls(op, table, schema=SCHEMA)


def downgrade() -> None:
    """Remove identity, customer, case, and audit tables and security configuration."""
    for table in reversed(TENANT_TABLES):
        disable_tenant_rls(op, table, schema=SCHEMA)
    for table in ALL_TABLES:
        op.execute(f'REVOKE ALL PRIVILEGES ON {SCHEMA}.{table} FROM enact_app')
    for table in reversed(ALL_TABLES):
        op.drop_table(table, schema=SCHEMA)
