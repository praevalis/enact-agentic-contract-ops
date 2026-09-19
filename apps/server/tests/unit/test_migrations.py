"""Unit tests for reusable database migration helpers."""

import pytest
from enact.platform.database.migrations import enable_tenant_rls
from sqlalchemy.sql import Executable


class _RecordingOperations:
    """Record migration statements without executing them."""

    def __init__(self) -> None:
        """Initialize an empty statement collection."""
        self.statements: list[Executable | str] = []

    def execute(self, sqltext: Executable | str) -> None:
        """Record one migration statement.

        Args:
            sqltext: Statement supplied by the migration helper.
        """
        self.statements.append(sqltext)


@pytest.mark.unit
class TestTenantRlsMigrations:
    """Verify validation performed before RLS SQL generation."""

    @pytest.mark.parametrize(
        ('table_name', 'schema'),
        [
            ('Customers', 'enact'),
            ('customers; DROP SCHEMA enact', 'enact'),
            ('customers', 'Enact'),
            ('customers', 'enact; DROP SCHEMA public'),
        ],
    )
    def test_enable_rejects_unsafe_identifiers(self, table_name: str, schema: str) -> None:
        operations = _RecordingOperations()

        with pytest.raises(ValueError, match='Invalid PostgreSQL identifier'):
            enable_tenant_rls(operations, table_name, schema=schema)

        assert operations.statements == []
