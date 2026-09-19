"""Integration tests for tenant row-level security."""

from typing import cast
from uuid import UUID, uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.platform.database.migrations import disable_tenant_rls, enable_tenant_rls
from enact.platform.database.session import (
    SessionManager,
    create_database_engine,
)
from sqlalchemy import Connection, text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

INSERT_PARENT = text(
    'INSERT INTO enact.rls_test_parents (organization_id, id, value) '
    'VALUES (:organization_id, :id, :value)'
)
INSERT_CHILD = text(
    'INSERT INTO enact.rls_test_children (organization_id, id, parent_id, value) '
    'VALUES (:organization_id, :id, :parent_id, :value)'
)
READ_PARENT_VALUE = text('SELECT value FROM enact.rls_test_parents WHERE id = :parent_id')
COUNT_VISIBLE_PARENT_CHILD_JOINS = text(
    'SELECT count(*) '
    'FROM enact.rls_test_parents AS parent '
    'JOIN enact.rls_test_children AS child '
    'ON child.organization_id = parent.organization_id '
    'AND child.parent_id = parent.id'
)


async def _insert_parent(
    manager: SessionManager,
    organization_id: UUID,
    parent_id: UUID,
    value: str,
) -> None:
    """Persist one parent through the tenant-scoped application role."""
    async with manager.tenant_session_scope(organization_id) as session:
        await session.execute(
            INSERT_PARENT,
            {
                'organization_id': str(organization_id),
                'id': str(parent_id),
                'value': value,
            },
        )
        await session.commit()


async def _insert_child(
    manager: SessionManager,
    organization_id: UUID,
    child_id: UUID,
    parent_id: UUID,
    value: str,
) -> None:
    """Persist one child through the tenant-scoped application role."""
    async with manager.tenant_session_scope(organization_id) as session:
        await session.execute(
            INSERT_CHILD,
            {
                'organization_id': str(organization_id),
                'id': str(child_id),
                'parent_id': str(parent_id),
                'value': value,
            },
        )
        await session.commit()


async def _read_parent_value(
    manager: SessionManager,
    organization_id: UUID,
    parent_id: UUID,
) -> str | None:
    """Read one parent value through a tenant-scoped application session."""
    async with manager.tenant_session_scope(organization_id) as session:
        return cast(
            str | None,
            await session.scalar(READ_PARENT_VALUE, {'parent_id': str(parent_id)}),
        )


async def _count_visible_joins(session: AsyncSession) -> int:
    """Count parent-child joins visible to the current database context."""
    count = cast(int | None, await session.scalar(COUNT_VISIBLE_PARENT_CHILD_JOINS))
    assert count is not None
    return count


def _enable_scratch_rls(connection: Connection, table_name: str) -> None:
    """Enable RLS on a scratch table through a real Alembic operations boundary."""
    enable_tenant_rls(Operations(MigrationContext.configure(connection)), table_name)


def _disable_scratch_rls(connection: Connection, table_name: str) -> None:
    """Disable RLS on a scratch table through a real Alembic operations boundary."""
    disable_tenant_rls(Operations(MigrationContext.configure(connection)), table_name)


@pytest.mark.integration
@pytest.mark.asyncio
class TestTenantRlsMigration:
    """Verify the reusable migration operations against PostgreSQL catalogs."""

    async def test_enable_and_disable_tenant_rls(
        self,
        rls_admin_database_url: str,
    ) -> None:
        table_name = f'rls_test_scratch_{uuid4().hex}'
        engine = create_database_engine(rls_admin_database_url)

        try:
            async with engine.begin() as connection:
                await connection.execute(text('SET LOCAL ROLE enact_owner'))
                await connection.execute(
                    text(
                        f'CREATE TABLE enact.{table_name} ('
                        'organization_id uuid NOT NULL, '
                        'id uuid NOT NULL'
                        ')'
                    )
                )
                await connection.run_sync(_enable_scratch_rls, table_name)

                flags = cast(
                    tuple[bool, bool] | None,
                    (
                        await connection.execute(
                            text(
                                'SELECT class.relrowsecurity, class.relforcerowsecurity '
                                'FROM pg_class AS class '
                                'JOIN pg_namespace AS namespace '
                                'ON namespace.oid = class.relnamespace '
                                'WHERE namespace.nspname = :schema '
                                'AND class.relname = :table_name'
                            ),
                            {'schema': 'enact', 'table_name': table_name},
                        )
                    )
                    .tuples()
                    .one_or_none(),
                )
                policy = (
                    (
                        await connection.execute(
                            text(
                                'SELECT roles, cmd, qual, with_check '
                                'FROM pg_policies '
                                'WHERE schemaname = :schema '
                                'AND tablename = :table_name '
                                'AND policyname = :policy_name'
                            ),
                            {
                                'schema': 'enact',
                                'table_name': table_name,
                                'policy_name': 'tenant_isolation',
                            },
                        )
                    )
                    .mappings()
                    .one_or_none()
                )

                assert flags == (True, True)
                assert policy is not None
                assert policy['roles'] == ['enact_app']
                assert policy['cmd'] == 'ALL'
                assert policy['qual'] == policy['with_check']
                assert 'enact.organization_id' in cast(str, policy['qual'])

                await connection.run_sync(_disable_scratch_rls, table_name)

                disabled_flags = cast(
                    tuple[bool, bool] | None,
                    (
                        await connection.execute(
                            text(
                                'SELECT class.relrowsecurity, class.relforcerowsecurity '
                                'FROM pg_class AS class '
                                'JOIN pg_namespace AS namespace '
                                'ON namespace.oid = class.relnamespace '
                                'WHERE namespace.nspname = :schema '
                                'AND class.relname = :table_name'
                            ),
                            {'schema': 'enact', 'table_name': table_name},
                        )
                    )
                    .tuples()
                    .one_or_none(),
                )
                policy_count = cast(
                    int | None,
                    await connection.scalar(
                        text(
                            'SELECT count(*) FROM pg_policies '
                            'WHERE schemaname = :schema '
                            'AND tablename = :table_name '
                            'AND policyname = :policy_name'
                        ),
                        {
                            'schema': 'enact',
                            'table_name': table_name,
                            'policy_name': 'tenant_isolation',
                        },
                    ),
                )

                assert disabled_flags == (False, False)
                assert policy_count == 0

                await connection.execute(text(f'DROP TABLE enact.{table_name}'))
        finally:
            await engine.dispose()


@pytest.mark.integration
@pytest.mark.asyncio
class TestTenantRlsIsolation:
    """Verify tenant isolation through the runtime application role."""

    async def test_reads_and_joins_are_tenant_isolated(
        self,
        rls_session_manager: SessionManager,
    ) -> None:
        organization_a = uuid4()
        organization_b = uuid4()
        parent_a = uuid4()
        parent_b = uuid4()

        await _insert_parent(rls_session_manager, organization_a, parent_a, 'tenant-a')
        await _insert_child(rls_session_manager, organization_a, uuid4(), parent_a, 'tenant-a')
        await _insert_parent(rls_session_manager, organization_b, parent_b, 'tenant-b')
        await _insert_child(rls_session_manager, organization_b, uuid4(), parent_b, 'tenant-b')

        async with rls_session_manager.tenant_session_scope(organization_a) as session:
            assert await _count_visible_joins(session) == 1
            assert (
                await session.scalar(
                    READ_PARENT_VALUE,
                    {'parent_id': str(parent_b)},
                )
                is None
            )

        async with rls_session_manager.tenant_session_scope(organization_b) as session:
            assert await _count_visible_joins(session) == 1

        async with rls_session_manager.tenant_session_scope(uuid4()) as session:
            assert await _count_visible_joins(session) == 0

        async with rls_session_manager.session_scope() as session:
            assert await _count_visible_joins(session) == 0

    async def test_inserts_require_matching_tenant_context(
        self,
        rls_session_manager: SessionManager,
    ) -> None:
        organization_a = uuid4()
        organization_b = uuid4()
        parent_a = uuid4()

        await _insert_parent(rls_session_manager, organization_a, parent_a, 'allowed')
        assert await _read_parent_value(rls_session_manager, organization_a, parent_a) == 'allowed'

        with pytest.raises(DBAPIError):
            async with rls_session_manager.tenant_session_scope(organization_a) as session:
                await session.execute(
                    INSERT_PARENT,
                    {
                        'organization_id': str(organization_b),
                        'id': str(uuid4()),
                        'value': 'cross-tenant',
                    },
                )

        with pytest.raises(DBAPIError):
            async with rls_session_manager.session_scope() as session:
                await session.execute(
                    INSERT_PARENT,
                    {
                        'organization_id': str(organization_a),
                        'id': str(uuid4()),
                        'value': 'unscoped',
                    },
                )

    async def test_updates_cannot_cross_tenant_boundary(
        self,
        rls_session_manager: SessionManager,
    ) -> None:
        organization_a = uuid4()
        organization_b = uuid4()
        parent_a = uuid4()
        parent_b = uuid4()

        await _insert_parent(rls_session_manager, organization_a, parent_a, 'tenant-a')
        await _insert_parent(rls_session_manager, organization_b, parent_b, 'tenant-b')

        async with rls_session_manager.tenant_session_scope(organization_a) as session:
            await session.execute(
                text('UPDATE enact.rls_test_parents SET value = :value WHERE id = :parent_id'),
                {'value': 'changed-by-a', 'parent_id': str(parent_b)},
            )
            await session.execute(
                text('UPDATE enact.rls_test_parents SET value = :value WHERE id = :parent_id'),
                {'value': 'updated-a', 'parent_id': str(parent_a)},
            )
            await session.commit()

        assert (
            await _read_parent_value(rls_session_manager, organization_a, parent_a) == 'updated-a'
        )
        assert await _read_parent_value(rls_session_manager, organization_b, parent_b) == 'tenant-b'

    async def test_deletes_cannot_cross_tenant_boundary(
        self,
        rls_session_manager: SessionManager,
    ) -> None:
        organization_a = uuid4()
        organization_b = uuid4()
        parent_a = uuid4()
        parent_b = uuid4()

        await _insert_parent(rls_session_manager, organization_a, parent_a, 'tenant-a')
        await _insert_parent(rls_session_manager, organization_b, parent_b, 'tenant-b')

        async with rls_session_manager.tenant_session_scope(organization_a) as session:
            await session.execute(
                text('DELETE FROM enact.rls_test_parents WHERE id = :parent_id'),
                {'parent_id': str(parent_b)},
            )
            await session.execute(
                text('DELETE FROM enact.rls_test_parents WHERE id = :parent_id'),
                {'parent_id': str(parent_a)},
            )
            await session.commit()

        assert await _read_parent_value(rls_session_manager, organization_a, parent_a) is None
        assert await _read_parent_value(rls_session_manager, organization_b, parent_b) == 'tenant-b'

    async def test_composite_foreign_key_rejects_cross_tenant_parent(
        self,
        rls_session_manager: SessionManager,
    ) -> None:
        organization_a = uuid4()
        organization_b = uuid4()
        parent_b = uuid4()

        await _insert_parent(rls_session_manager, organization_b, parent_b, 'tenant-b')

        with pytest.raises(IntegrityError):
            async with rls_session_manager.tenant_session_scope(organization_a) as session:
                await session.execute(
                    INSERT_CHILD,
                    {
                        'organization_id': str(organization_a),
                        'id': str(uuid4()),
                        'parent_id': str(parent_b),
                        'value': 'cross-tenant-reference',
                    },
                )
