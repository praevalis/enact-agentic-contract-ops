"""Case creation, lineage, and tenant isolation in PostgreSQL."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.cases.errors import CaseNotFoundError
from enact.cases.schemas import CaseType
from enact.cases.services import CaseService
from enact.customers.errors import CustomerNotFoundError
from enact.customers.services import CustomerService
from enact.identity.authentication import Principal
from enact.infrastructure.database import Base
from enact.infrastructure.database.migrations import enable_tenant_rls
from enact.infrastructure.database.models.audit import AuditEvent
from enact.infrastructure.database.models.cases import Case, CaseLineage
from enact.infrastructure.database.models.customers import Customer
from enact.infrastructure.database.models.identity import Organization, User
from enact.infrastructure.database.session import SessionManager, create_database_engine
from enact.infrastructure.database.uows.cases import SqlAlchemyCaseUnitOfWork
from enact.infrastructure.database.uows.customers import SqlAlchemyCustomerUnitOfWork
from sqlalchemy import Connection, func, insert, select, text, update
from sqlalchemy.exc import IntegrityError


def _create_case_and_customer_tables(connection: Connection) -> None:
    """Create only the persistence tables needed by case and customer creation."""
    Base.metadata.create_all(
        connection,
        tables=[
            Base.metadata.tables['enact.organizations'],
            Base.metadata.tables['enact.users'],
            Base.metadata.tables['enact.customers'],
            Base.metadata.tables['enact.cases'],
            Base.metadata.tables['enact.case_lineage'],
            Base.metadata.tables['enact.audit_events'],
        ],
    )


def _enable_case_and_customer_rls(connection: Connection) -> None:
    """Apply the production RLS policy to case- and customer-owned tables."""
    operations = Operations(MigrationContext.configure(connection))
    for table in ('customers', 'cases', 'case_lineage', 'audit_events'):
        enable_tenant_rls(operations, table)


@pytest.mark.integration
@pytest.mark.asyncio
class TestCaseIsolation:
    """Verify case effects stay inside the authorized tenant."""

    async def test_creation_lineage_and_audit_are_tenant_scoped(
        self, rls_admin_database_url: str, rls_session_manager: SessionManager
    ) -> None:
        organization_a, organization_b = uuid4(), uuid4()
        actor_id = uuid4()
        now = datetime.now(UTC)
        engine = create_database_engine(rls_admin_database_url)

        try:
            async with engine.begin() as connection:
                await connection.execute(text('SET LOCAL ROLE enact_owner'))
                await connection.run_sync(_create_case_and_customer_tables)
                await connection.execute(
                    insert(Organization),
                    [
                        {'id': organization_a, 'name': 'Tenant A', 'status': 'active'},
                        {'id': organization_b, 'name': 'Tenant B', 'status': 'active'},
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
                await connection.run_sync(_enable_case_and_customer_rls)
                await connection.execute(
                    text(
                        'GRANT SELECT, INSERT, UPDATE, DELETE ON '
                        'enact.organizations, enact.users, enact.customers, '
                        'enact.cases, enact.case_lineage TO enact_app'
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

            async with rls_session_manager.session_scope() as session:
                service = CaseService(uow=SqlAlchemyCaseUnitOfWork(session), clock=lambda: now)
                baseline = await service.create(
                    principal=principal,
                    customer_id=customer.id,
                    title='Baseline',
                    case_type=CaseType.ACTIVATION,
                    prior_case_id=None,
                )

            async with rls_session_manager.session_scope() as session:
                service = CaseService(uow=SqlAlchemyCaseUnitOfWork(session), clock=lambda: now)
                amendment = await service.create(
                    principal=principal,
                    customer_id=customer.id,
                    title='Amendment',
                    case_type=CaseType.AMENDMENT,
                    prior_case_id=baseline.id,
                )

            async with engine.begin() as connection:
                await connection.execute(
                    update(Case)
                    .where(Case.id.in_((baseline.id, amendment.id)))
                    .values(created_at=now)
                )

            async with rls_session_manager.session_scope() as session:
                service = CaseService(uow=SqlAlchemyCaseUnitOfWork(session))
                detail = await service.get(principal=principal, case_id=amendment.id)
                first = await service.list(principal=principal, page_size=1)
                assert first.next_cursor is not None
                second = await service.list(
                    principal=principal, page_size=1, cursor=first.next_cursor
                )
                filtered = await service.list(
                    principal=principal,
                    page_size=25,
                    customer_id=customer.id,
                    case_type=CaseType.AMENDMENT,
                    status='draft',
                )

            assert detail.prior_case_id == baseline.id
            assert first.items[0].id == max(baseline.id, amendment.id)
            assert second.items[0].id == min(baseline.id, amendment.id)
            assert second.next_cursor is None
            assert [item.id for item in filtered.items] == [amendment.id]
            assert filtered.items[0].prior_case_id == baseline.id

            foreign_principal = Principal(
                user_id=actor_id,
                organization_id=organization_b,
                membership_id=uuid4(),
                role='deal_desk',
                session_id=uuid4(),
                access_token_expires_at=now + timedelta(minutes=15),
            )
            async with rls_session_manager.session_scope() as session:
                service = CaseService(uow=SqlAlchemyCaseUnitOfWork(session))
                with pytest.raises(CustomerNotFoundError):
                    await service.create(
                        principal=foreign_principal,
                        customer_id=customer.id,
                        title='Foreign customer',
                        case_type=CaseType.ACTIVATION,
                        prior_case_id=None,
                    )

            async with rls_session_manager.session_scope() as session:
                service = CaseService(uow=SqlAlchemyCaseUnitOfWork(session))
                assert (await service.list(principal=foreign_principal, page_size=25)).items == []

                with pytest.raises(CaseNotFoundError):
                    await service.get(principal=foreign_principal, case_id=amendment.id)

            async with rls_session_manager.tenant_session_scope(organization_b) as session:
                assert await session.scalar(select(func.count()).select_from(Customer)) == 0
                assert await session.scalar(select(func.count()).select_from(Case)) == 0
                assert await session.scalar(select(func.count()).select_from(CaseLineage)) == 0
                assert await session.scalar(select(func.count()).select_from(AuditEvent)) == 0

            async with rls_session_manager.session_scope() as session:
                assert await session.scalar(select(func.count()).select_from(Case)) == 0

            async with engine.begin() as connection:
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(Customer)
                        .where(Customer.organization_id == organization_a)
                    )
                    == 1
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(Case)
                        .where(Case.organization_id == organization_a)
                    )
                    == 2
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(CaseLineage)
                        .where(CaseLineage.organization_id == organization_a)
                    )
                    == 1
                )
                assert (
                    await connection.scalar(
                        select(func.count())
                        .select_from(AuditEvent)
                        .where(AuditEvent.organization_id == organization_a)
                    )
                    == 3
                )
                edge = (
                    await connection.execute(
                        select(CaseLineage.source_case_id, CaseLineage.target_case_id).where(
                            CaseLineage.organization_id == organization_a
                        )
                    )
                ).one()
                assert edge == (baseline.id, amendment.id)

            # A distinct predecessor must not be attached to the same amendment case.
            with pytest.raises(IntegrityError, match='uq_case_lineage_amends_target'):
                async with engine.begin() as connection:
                    other_prior_case_id = uuid4()
                    await connection.execute(
                        insert(Case).values(
                            id=other_prior_case_id,
                            organization_id=organization_a,
                            customer_id=customer.id,
                            title='Other baseline',
                            case_type='activation',
                        )
                    )
                    await connection.execute(
                        insert(CaseLineage).values(
                            organization_id=organization_a,
                            source_case_id=other_prior_case_id,
                            target_case_id=amendment.id,
                            relationship_type='amends',
                        )
                    )
        finally:
            async with engine.begin() as connection:
                for table in ('customers', 'cases', 'case_lineage', 'audit_events'):
                    await connection.execute(
                        text(f'DROP POLICY IF EXISTS tenant_isolation ON enact.{table}')
                    )
            await engine.dispose()
