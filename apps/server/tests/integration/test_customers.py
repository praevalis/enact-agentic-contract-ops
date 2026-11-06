"""Customer creation and tenant isolation in PostgreSQL."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.customers.services import CustomerService
from enact.identity.authentication import Principal
from enact.infrastructure.database import Base
from enact.infrastructure.database.migrations import enable_tenant_rls
from enact.infrastructure.database.models.audit import AuditEvent
from enact.infrastructure.database.models.customers import Customer
from enact.infrastructure.database.models.identity import Organization, User
from enact.infrastructure.database.session import SessionManager, create_database_engine
from enact.infrastructure.database.uows.customers import SqlAlchemyCustomerUnitOfWork
from sqlalchemy import Connection, func, insert, select, text


def _create_customer_tables(connection: Connection) -> None:
    """Create the tables needed for customer creation and its audit event."""
    Base.metadata.create_all(
        connection,
        tables=[
            Base.metadata.tables['enact.organizations'],
            Base.metadata.tables['enact.users'],
            Base.metadata.tables['enact.customers'],
            Base.metadata.tables['enact.audit_events'],
        ],
    )


def _enable_customer_rls(connection: Connection) -> None:
    """Apply production RLS policies to customer and audit records."""
    operations = Operations(MigrationContext.configure(connection))
    for table in ('customers', 'audit_events'):
        enable_tenant_rls(operations, table)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCustomerIsolation:
    """Verify customer creation and audit writes stay in the active tenant."""

    async def test_created_customer_is_hidden_from_other_tenants(
        self, rls_admin_database_url: str, rls_session_manager: SessionManager
    ) -> None:
        """Require RLS context for customer and audit visibility."""
        organization_a, organization_b = uuid4(), uuid4()
        actor_id = uuid4()
        now = datetime.now(UTC)
        engine = create_database_engine(rls_admin_database_url)

        try:
            async with engine.begin() as connection:
                await connection.execute(text('SET LOCAL ROLE enact_owner'))
                await connection.run_sync(_create_customer_tables)
                await connection.execute(
                    insert(Organization),
                    [
                        {'id': organization_a, 'name': 'Customer Tenant A', 'status': 'active'},
                        {'id': organization_b, 'name': 'Customer Tenant B', 'status': 'active'},
                    ],
                )
                await connection.execute(
                    insert(User).values(
                        id=actor_id,
                        email=f'{actor_id}@example.com',
                        password_hash='test',
                        display_name='Deal Desk',
                        status='active',
                    )
                )
                await connection.run_sync(_enable_customer_rls)
                await connection.execute(
                    text(
                        'GRANT SELECT, INSERT, UPDATE, DELETE ON '
                        'enact.organizations, enact.users, enact.customers TO enact_app'
                    )
                )
                await connection.execute(
                    text('GRANT SELECT, INSERT ON enact.audit_events TO enact_app')
                )

            principal = Principal(
                user_id=actor_id,
                organization_id=organization_a,
                membership_id=uuid4(),
                role='deal_desk',
                session_id=uuid4(),
                access_token_expires_at=now + timedelta(minutes=15),
            )

            async with rls_session_manager.session_scope() as session:
                service = CustomerService(
                    uow=SqlAlchemyCustomerUnitOfWork(session), clock=lambda: now
                )
                customer = await service.create(principal=principal, display_name='Redwood Systems')

            async with rls_session_manager.tenant_session_scope(organization_b) as session:
                assert await session.scalar(select(func.count()).select_from(Customer)) == 0
                assert await session.scalar(select(func.count()).select_from(AuditEvent)) == 0

            async with rls_session_manager.session_scope() as session:
                assert await session.scalar(select(func.count()).select_from(Customer)) == 0

            async with engine.begin() as connection:
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(Customer)
                        .where(
                            Customer.organization_id == organization_a, Customer.id == customer.id
                        )
                    )
                    == 1
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(AuditEvent)
                        .where(AuditEvent.organization_id == organization_a)
                    )
                    == 1
                )
        finally:
            async with engine.begin() as connection:
                for table in ('customers', 'audit_events'):
                    await connection.execute(
                        text(f'DROP POLICY IF EXISTS tenant_isolation ON enact.{table}')
                    )
            await engine.dispose()
