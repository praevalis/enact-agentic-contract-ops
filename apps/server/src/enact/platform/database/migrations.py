"""Reusable security operations for Alembic migrations."""

import re
from typing import Protocol

from sqlalchemy.sql import Executable

IDENTIFIER_PATTERN = re.compile(r'^[a-z_][a-z0-9_]*$')
DEFAULT_SCHEMA = 'enact'
ORGANIZATION_COLUMN = 'organization_id'
POLICY_NAME = 'tenant_isolation'
RUNTIME_ROLE = 'enact_app'
TENANT_SETTING = 'enact.organization_id'


class _MigrationOperations(Protocol):
    """Migration operation required by the RLS helpers."""

    def execute(self, sqltext: Executable | str) -> None:
        """Execute a migration statement."""


def enable_tenant_rls(
    operations: _MigrationOperations,
    table_name: str,
    *,
    schema: str = DEFAULT_SCHEMA,
) -> None:
    """Enable fail-closed tenant isolation on a table.

    Args:
        operations: Alembic operations boundary used to execute migration SQL.
        table_name: Tenant-owned table containing a UUID ``organization_id`` column.
        schema: Schema containing the tenant-owned table.

    Raises:
        ValueError: If the schema or table name is not a safe PostgreSQL identifier.
    """
    qualified_table = _qualified_table(schema, table_name)
    policy_name = _quote_identifier(POLICY_NAME)
    runtime_role = _quote_identifier(RUNTIME_ROLE)
    organization_column = _quote_identifier(ORGANIZATION_COLUMN)
    tenant_expression = (
        f"{organization_column} = NULLIF(current_setting('{TENANT_SETTING}', true), '')::uuid"
    )

    operations.execute(f'ALTER TABLE {qualified_table} ENABLE ROW LEVEL SECURITY')
    operations.execute(f'ALTER TABLE {qualified_table} FORCE ROW LEVEL SECURITY')
    operations.execute(
        f'CREATE POLICY {policy_name} ON {qualified_table} '
        f'FOR ALL TO {runtime_role} '
        f'USING ({tenant_expression}) '
        f'WITH CHECK ({tenant_expression})'
    )


def disable_tenant_rls(
    operations: _MigrationOperations,
    table_name: str,
    *,
    schema: str = DEFAULT_SCHEMA,
) -> None:
    """Remove tenant isolation from a table during downgrade.

    Args:
        operations: Alembic operations boundary used to execute migration SQL.
        table_name: Tenant-owned table from which to remove RLS.
        schema: Schema containing the tenant-owned table.

    Raises:
        ValueError: If the schema or table name is not a safe PostgreSQL identifier.
    """
    qualified_table = _qualified_table(schema, table_name)
    policy_name = _quote_identifier(POLICY_NAME)

    operations.execute(f'DROP POLICY {policy_name} ON {qualified_table}')
    operations.execute(f'ALTER TABLE {qualified_table} NO FORCE ROW LEVEL SECURITY')
    operations.execute(f'ALTER TABLE {qualified_table} DISABLE ROW LEVEL SECURITY')


def _qualified_table(schema: str, table_name: str) -> str:
    """Return a safely quoted schema-qualified table name."""
    return f'{_quote_identifier(schema)}.{_quote_identifier(table_name)}'


def _quote_identifier(identifier: str) -> str:
    """Validate and quote a PostgreSQL identifier."""
    if IDENTIFIER_PATTERN.fullmatch(identifier) is None:
        raise ValueError(f'Invalid PostgreSQL identifier: {identifier!r}.')

    return f'"{identifier}"'
