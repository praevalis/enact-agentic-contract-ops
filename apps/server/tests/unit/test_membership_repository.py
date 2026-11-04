"""Unit tests for guarded membership persistence transitions."""

from typing import cast
from uuid import UUID, uuid4

import pytest
from enact.identity.errors import MembershipTransitionError
from enact.infrastructure.database.models.identity import Membership as MembershipModel
from enact.infrastructure.database.repositories import SqlAlchemyMembershipRepository
from sqlalchemy.ext.asyncio import AsyncSession


class _Session:
    """Hold a membership row and record transition locking."""

    def __init__(self, model: MembershipModel) -> None:
        self.model = model
        self.lock_count = 0
        self.flush_count = 0

    async def get(
        self,
        entity: type[MembershipModel],
        membership_id: UUID,
        *,
        with_for_update: bool = False,
    ) -> MembershipModel | None:
        assert entity is MembershipModel
        if with_for_update:
            self.lock_count += 1
        return self.model if self.model.id == membership_id else None

    async def flush(self) -> None:
        self.flush_count += 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestSqlAlchemyMembershipRepository:
    """Verify persistence guards prevent invalid membership transitions."""

    async def test_transitions_lock_row_and_preserve_regrant_identity(self) -> None:
        """Require explicit regrant after revocation and retain the membership row."""
        model = MembershipModel(
            id=uuid4(),
            user_id=uuid4(),
            organization_id=uuid4(),
            role='auditor',
            status='active',
        )
        session = _Session(model)
        repository = SqlAlchemyMembershipRepository(cast(AsyncSession, session))

        suspended = await repository.suspend(model.id)
        resumed = await repository.resume(model.id)
        revoked = await repository.revoke(model.id)
        with pytest.raises(MembershipTransitionError):
            await repository.resume(model.id)
        regranted = await repository.regrant(model.id, 'deal_desk')

        assert suspended.status == 'suspended'
        assert resumed.status == 'active' and resumed.role == 'auditor'
        assert revoked.status == 'revoked'
        assert regranted.id == model.id
        assert regranted.status == 'active' and regranted.role == 'deal_desk'
        assert session.lock_count == 5
        assert session.flush_count == 4
