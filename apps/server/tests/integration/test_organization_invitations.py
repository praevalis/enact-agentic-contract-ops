"""PostgreSQL isolation checks for invitation-code redemption."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from enact.infrastructure.database.migrations import enable_tenant_rls
from enact.infrastructure.database.session import SessionManager, create_database_engine
from sqlalchemy import Connection, text


def _enable_invitation_rls(connection: Connection, schema: str) -> None:
    """Apply tenant and code capability policies to a disposable invitation table."""
    operations = Operations(MigrationContext.configure(connection))
    enable_tenant_rls(operations, 'organization_invitations', schema=schema)
    operations.execute(
        f'CREATE POLICY invitation_code_lookup ON {schema}.organization_invitations '
        'FOR SELECT TO enact_app USING ('
        "code_digest = NULLIF(current_setting('enact.invitation_digest', true), '')"
        ')'
    )
    operations.execute(
        f'CREATE POLICY invitation_code_redeem ON {schema}.organization_invitations '
        'FOR UPDATE TO enact_app '
        "USING (code_digest = NULLIF(current_setting('enact.invitation_digest', true), '')) "
        "WITH CHECK (code_digest = NULLIF(current_setting('enact.invitation_digest', true), ''))"
    )


@pytest.mark.integration
@pytest.mark.asyncio
class TestOrganizationInvitationIsolation:
    """Verify tenant RLS and code-scoped redemption through the app role."""

    async def test_code_exposes_only_its_row_and_redeems_once(
        self,
        rls_admin_database_url: str,
        rls_session_manager: SessionManager,
    ) -> None:
        """Keep invitations hidden without tenant or matching bearer-code context."""
        schema = f'onboarding_rls_{uuid4().hex}'
        organization_a, organization_b = uuid4(), uuid4()
        invitation_a, invitation_b = uuid4(), uuid4()
        engine = create_database_engine(rls_admin_database_url)

        try:
            async with engine.begin() as connection:
                await connection.execute(text(f'CREATE SCHEMA {schema} AUTHORIZATION enact_owner'))
                await connection.execute(text('SET LOCAL ROLE enact_owner'))
                await connection.execute(
                    text(
                        f'CREATE TABLE {schema}.organization_invitations ('
                        'id uuid PRIMARY KEY, organization_id uuid NOT NULL, '
                        'code_digest text NOT NULL UNIQUE, redeemed_at timestamptz)'
                    )
                )
                await connection.execute(
                    text(
                        f'INSERT INTO {schema}.organization_invitations '
                        '(id, organization_id, code_digest) VALUES '
                        '(:invitation_a, :organization_a, :digest_a), '
                        '(:invitation_b, :organization_b, :digest_b)'
                    ),
                    {
                        'invitation_a': str(invitation_a),
                        'organization_a': str(organization_a),
                        'digest_a': 'a' * 64,
                        'invitation_b': str(invitation_b),
                        'organization_b': str(organization_b),
                        'digest_b': 'b' * 64,
                    },
                )
                await connection.run_sync(_enable_invitation_rls, schema)
                await connection.execute(text(f'GRANT USAGE ON SCHEMA {schema} TO enact_app'))
                await connection.execute(
                    text(
                        f'GRANT SELECT, INSERT, UPDATE, DELETE ON '
                        f'{schema}.organization_invitations TO enact_app'
                    )
                )

            async with rls_session_manager.session_scope() as session:
                query = text(f'SELECT id FROM {schema}.organization_invitations')
                assert (await session.scalars(query)).all() == []

                await session.execute(
                    text("SELECT set_config('enact.invitation_digest', :digest, true)"),
                    {'digest': 'b' * 64},
                )
                assert (await session.scalars(query)).all() == [invitation_b]

                claim = text(
                    f'UPDATE {schema}.organization_invitations '
                    'SET redeemed_at = :redeemed_at '
                    'WHERE code_digest = :digest AND redeemed_at IS NULL RETURNING id'
                )
                parameters = {'redeemed_at': datetime.now(UTC), 'digest': 'b' * 64}
                assert (await session.scalars(claim, parameters)).all() == [invitation_b]
                assert (await session.scalars(claim, parameters)).all() == []
                await session.commit()

            async with rls_session_manager.tenant_session_scope(organization_a) as session:
                assert (await session.scalars(query)).all() == [invitation_a]
        finally:
            async with engine.begin() as connection:
                await connection.execute(text(f'DROP SCHEMA IF EXISTS {schema} CASCADE'))
            await engine.dispose()
