"""Add user-scoped membership discovery RLS."""

from collections.abc import Sequence

from alembic import op

revision: str = '0003_membership_discovery'
down_revision: str | None = '0002_auth_sessions'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'
MEMBERSHIPS = f'{SCHEMA}.memberships'
RUNTIME_ROLE = 'enact_app'


def _tenant_expression() -> str:
    """Return the transaction-local organization predicate."""
    return "organization_id = NULLIF(current_setting('enact.organization_id', true), '')::uuid"


def _user_expression() -> str:
    """Return the transaction-local user predicate."""
    return "user_id = NULLIF(current_setting('enact.user_id', true), '')::uuid"


def upgrade() -> None:
    """Allow authenticated users to discover their own memberships before org selection."""
    op.execute(f'DROP POLICY tenant_isolation ON {MEMBERSHIPS}')
    op.execute(
        f'CREATE POLICY membership_tenant_access ON {MEMBERSHIPS} '
        f'FOR ALL TO {RUNTIME_ROLE} '
        f'USING ({_tenant_expression()}) '
        f'WITH CHECK ({_tenant_expression()})'
    )
    op.execute(
        f'CREATE POLICY membership_user_discovery ON {MEMBERSHIPS} '
        f'FOR SELECT TO {RUNTIME_ROLE} '
        f'USING ({_user_expression()})'
    )


def downgrade() -> None:
    """Restore organization-only membership RLS."""
    op.execute(f'DROP POLICY membership_user_discovery ON {MEMBERSHIPS}')
    op.execute(f'DROP POLICY membership_tenant_access ON {MEMBERSHIPS}')
    op.execute(
        f'CREATE POLICY tenant_isolation ON {MEMBERSHIPS} '
        f'FOR ALL TO {RUNTIME_ROLE} '
        f'USING ({_tenant_expression()}) '
        f'WITH CHECK ({_tenant_expression()})'
    )
