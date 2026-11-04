"""Integration checks for membership changes under tenant row-level security."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.identity.errors import MembershipNotFoundError
from enact.identity.services import MembershipService
from enact.infrastructure.database import Base
from enact.infrastructure.database.migrations import enable_tenant_rls
from enact.infrastructure.database.models.audit import AuditEvent
from enact.infrastructure.database.models.auth import AuthSession
from enact.infrastructure.database.models.identity import Membership, Organization, User
from enact.infrastructure.database.session import SessionManager, create_database_engine
from enact.infrastructure.database.uows import SqlAlchemyIdentityUnitOfWork
from sqlalchemy import Connection, func, insert, select, text


def _create_identity_tables(connection: Connection) -> None:
    """Create the identity tables required by this test."""
    Base.metadata.create_all(
        connection,
        tables=[
            Base.metadata.tables['enact.organizations'],
            Base.metadata.tables['enact.users'],
            Base.metadata.tables['enact.memberships'],
            Base.metadata.tables['enact.auth_sessions'],
            Base.metadata.tables['enact.audit_events'],
        ],
    )


def _enable_identity_rls(connection: Connection) -> None:
    """Apply production tenant RLS policies to membership and audit tables."""
    operations = Operations(MigrationContext.configure(connection))
    enable_tenant_rls(operations, 'memberships')
    enable_tenant_rls(operations, 'audit_events')


@pytest.mark.integration
@pytest.mark.asyncio
class TestMembershipLifecycleIsolation:
    """Verify membership mutations, session effects, and audit stay tenant scoped."""

    async def test_suspend_is_atomic_and_cannot_target_another_organization(
        self,
        rls_admin_database_url: str,
        rls_session_manager: SessionManager,
    ) -> None:
        """Suspend one tenant's membership while preserving another tenant's rows."""
        organization_a, organization_b = uuid4(), uuid4()
        actor_id, target_a_id, target_b_id = uuid4(), uuid4(), uuid4()
        actor_membership_id, membership_a_id, membership_b_id = uuid4(), uuid4(), uuid4()
        auth_session_id = uuid4()
        now = datetime.now(UTC)
        engine = create_database_engine(rls_admin_database_url)

        try:
            async with engine.begin() as connection:
                await connection.execute(text('SET LOCAL ROLE enact_owner'))
                await connection.run_sync(_create_identity_tables)
                await connection.execute(
                    insert(Organization),
                    [
                        {'id': organization_a, 'name': 'Tenant A', 'status': 'active'},
                        {'id': organization_b, 'name': 'Tenant B', 'status': 'active'},
                    ],
                )
                await connection.execute(
                    insert(User),
                    [
                        {
                            'id': user_id,
                            'email': f'{user_id}@example.com',
                            'password_hash': 'test',
                            'display_name': 'Test User',
                            'status': 'active',
                        }
                        for user_id in (actor_id, target_a_id, target_b_id)
                    ],
                )
                await connection.execute(
                    insert(Membership),
                    [
                        {
                            'id': actor_membership_id,
                            'organization_id': organization_a,
                            'user_id': actor_id,
                            'role': 'administrator',
                            'status': 'active',
                        },
                        {
                            'id': membership_a_id,
                            'organization_id': organization_a,
                            'user_id': target_a_id,
                            'role': 'auditor',
                            'status': 'active',
                        },
                        {
                            'id': membership_b_id,
                            'organization_id': organization_b,
                            'user_id': target_b_id,
                            'role': 'auditor',
                            'status': 'active',
                        },
                    ],
                )
                await connection.execute(
                    insert(AuthSession).values(
                        id=auth_session_id,
                        user_id=target_a_id,
                        current_organization_id=organization_a,
                        token_family_id=uuid4(),
                        refresh_token_digest=uuid4().hex,
                        expires_at=now + timedelta(days=1),
                    )
                )
                await connection.run_sync(_enable_identity_rls)
                await connection.execute(
                    text(
                        'GRANT SELECT, INSERT, UPDATE, DELETE ON '
                        'enact.organizations, enact.users, enact.memberships, '
                        'enact.auth_sessions TO enact_app'
                    )
                )
                await connection.execute(
                    text('GRANT SELECT, INSERT ON enact.audit_events TO enact_app')
                )

            now = datetime.now(UTC)
            async with rls_session_manager.tenant_session_scope(organization_a) as session:
                service = MembershipService(
                    uow=SqlAlchemyIdentityUnitOfWork(session), clock=lambda: now
                )
                suspended = await service.suspend(
                    actor_user_id=actor_id,
                    organization_id=organization_a,
                    membership_id=membership_a_id,
                )
                assert suspended.status == 'suspended'

            async with rls_session_manager.tenant_session_scope(organization_a) as session:
                service = MembershipService(
                    uow=SqlAlchemyIdentityUnitOfWork(session), clock=lambda: now
                )
                with pytest.raises(MembershipNotFoundError):
                    await service.revoke(
                        actor_user_id=actor_id,
                        organization_id=organization_a,
                        membership_id=membership_b_id,
                    )

            async with rls_session_manager.tenant_session_scope(organization_b) as session:
                visible_audit_events = await session.scalar(
                    select(func.count()).select_from(AuditEvent)
                )
                assert visible_audit_events == 0

            async with engine.begin() as connection:
                memberships = dict(
                    (
                        await connection.execute(
                            select(Membership.id, Membership.status).where(
                                Membership.id.in_((membership_a_id, membership_b_id))
                            )
                        )
                    )
                    .tuples()
                    .all()
                )
                revoked_at = await connection.scalar(
                    select(AuthSession.revoked_at).where(AuthSession.id == auth_session_id)
                )
                events = (
                    (
                        await connection.execute(
                            select(
                                AuditEvent.organization_id,
                                AuditEvent.actor_user_id,
                                AuditEvent.action,
                            ).where(AuditEvent.resource_id == membership_a_id)
                        )
                    )
                    .tuples()
                    .all()
                )

            assert memberships == {membership_a_id: 'suspended', membership_b_id: 'active'}
            assert revoked_at is not None
            assert len(events) == 1
            assert events[0] == (organization_a, actor_id, 'membership.suspend')
        finally:
            await engine.dispose()
