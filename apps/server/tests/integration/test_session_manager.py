"""Integration tests for asynchronous database session management."""

from typing import cast
from uuid import uuid4

import pytest
from enact.platform.database.session import SessionManager
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_CURRENT_ORGANIZATION_ID = text("SELECT NULLIF(current_setting('enact.organization_id', true), '')")
_BACKEND_PROCESS_ID = text('SELECT pg_backend_pid()')


async def _get_current_organization_id(session: AsyncSession) -> str | None:
    """Return the transaction-local organization identifier when configured."""
    return cast(str | None, await session.scalar(_CURRENT_ORGANIZATION_ID))


async def _get_backend_process_id(session: AsyncSession) -> int:
    """Return the PostgreSQL process identifier serving the session."""
    process_id = cast(int | None, await session.scalar(_BACKEND_PROCESS_ID))
    assert process_id is not None
    return process_id


@pytest.mark.integration
class TestSessionManagerTenantScope:
    """Verify transaction-local tenant session behavior."""

    @pytest.mark.asyncio
    async def test_sets_tenant_context_for_current_transaction(
        self,
        session_manager: SessionManager,
    ) -> None:
        organization_id = uuid4()

        async with session_manager.tenant_session_scope(organization_id) as session:
            configured_id = await _get_current_organization_id(session)

        assert configured_id == str(organization_id)

    @pytest.mark.asyncio
    async def test_commit_clears_tenant_context(
        self,
        session_manager: SessionManager,
    ) -> None:
        async with session_manager.tenant_session_scope(uuid4()) as session:
            tenant_process_id = await _get_backend_process_id(session)
            await session.commit()

            unscoped_process_id = await _get_backend_process_id(session)
            configured_id = await _get_current_organization_id(session)

        assert unscoped_process_id == tenant_process_id
        assert configured_id is None

    @pytest.mark.asyncio
    async def test_rollback_clears_tenant_context_before_pool_reuse(
        self,
        session_manager: SessionManager,
    ) -> None:
        tenant_process_id: int | None = None

        with pytest.raises(RuntimeError, match='force tenant transaction rollback'):
            async with session_manager.tenant_session_scope(uuid4()) as session:
                tenant_process_id = await _get_backend_process_id(session)
                raise RuntimeError('force tenant transaction rollback')

        async with session_manager.session_scope() as session:
            unscoped_process_id = await _get_backend_process_id(session)
            configured_id = await _get_current_organization_id(session)

        assert tenant_process_id is not None
        assert unscoped_process_id == tenant_process_id
        assert configured_id is None
