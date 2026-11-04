"""Unit tests for membership lifecycle orchestration."""

from dataclasses import replace
from datetime import UTC, datetime
from types import TracebackType
from typing import cast
from uuid import UUID, uuid4

import pytest
from enact.identity.entities import Membership
from enact.identity.enums import MembershipRole
from enact.identity.errors import (
    MembershipNotFoundError,
    MembershipPermissionDeniedError,
    MembershipTransitionError,
)
from enact.identity.services import MembershipService
from enact.identity.unit_of_work import IdentityUnitOfWork


class _Memberships:
    """Keep actor and target memberships for service behavior tests."""

    def __init__(self, *memberships: Membership) -> None:
        self.items = {membership.id: membership for membership in memberships}

    async def get(self, membership_id: UUID) -> Membership | None:
        return self.items.get(membership_id)

    async def get_for_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Membership | None:
        return next(
            (
                membership
                for membership in self.items.values()
                if membership.user_id == user_id and membership.organization_id == organization_id
            ),
            None,
        )

    async def suspend(self, membership_id: UUID) -> Membership:
        return self._change(membership_id, 'active', 'suspended')

    async def resume(self, membership_id: UUID) -> Membership:
        return self._change(membership_id, 'suspended', 'active')

    async def revoke(self, membership_id: UUID) -> Membership:
        membership = self.items[membership_id]
        if membership.status not in {'active', 'suspended'}:
            raise MembershipTransitionError(membership_id, 'revoked')
        return self._change(membership_id, membership.status, 'revoked')

    async def regrant(self, membership_id: UUID, role: str) -> Membership:
        membership = self._change(membership_id, 'revoked', 'active')
        updated = replace(membership, role=role)
        self.items[membership_id] = updated
        return updated

    def _change(self, membership_id: UUID, expected: str, status: str) -> Membership:
        membership = self.items[membership_id]
        if membership.status != expected:
            raise MembershipTransitionError(membership_id, status)
        updated = replace(membership, status=status)
        self.items[membership_id] = updated
        return updated


class _Sessions:
    """Capture organization session revocations."""

    def __init__(self) -> None:
        self.revocations: list[tuple[UUID, UUID, datetime]] = []

    async def revoke_for_user_and_organization(
        self, user_id: UUID, organization_id: UUID, revoked_at: datetime
    ) -> None:
        self.revocations.append((user_id, organization_id, revoked_at))


class _AuditEvents:
    """Capture immutable audit event writes."""

    def __init__(self) -> None:
        self.actions: list[tuple[UUID, UUID, str, UUID, datetime, dict[str, object] | None]] = []

    async def create(
        self,
        *,
        organization_id: UUID,
        actor_user_id: UUID,
        action: str,
        resource_type: str,
        resource_id: UUID,
        occurred_at: datetime,
        details: dict[str, object] | None = None,
    ) -> None:
        assert resource_type == 'membership'
        self.actions.append(
            (organization_id, actor_user_id, action, resource_id, occurred_at, details)
        )


class _UnitOfWork:
    """Group membership effects within a recording transaction."""

    def __init__(self, memberships: _Memberships) -> None:
        self.memberships = memberships
        self.sessions = _Sessions()
        self.audit_events = _AuditEvents()
        self.commit_count = 0
        self.rollback_count = 0

    async def set_organization_context(self, organization_id: UUID) -> None:
        self.organization_context = organization_id

    async def __aenter__(self) -> '_UnitOfWork':
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            self.commit_count += 1
        else:
            self.rollback_count += 1


def _fixture(
    *, actor_role: MembershipRole = MembershipRole.ADMINISTRATOR
) -> tuple[MembershipService, _UnitOfWork, Membership, Membership, datetime]:
    organization_id = uuid4()
    actor = Membership(uuid4(), uuid4(), organization_id, actor_role.value, 'active')
    target = Membership(uuid4(), uuid4(), organization_id, MembershipRole.AUDITOR.value, 'active')
    uow = _UnitOfWork(_Memberships(actor, target))
    now = datetime(2026, 10, 25, tzinfo=UTC)
    service = MembershipService(uow=cast(IdentityUnitOfWork, uow), clock=lambda: now)
    return service, uow, actor, target, now


@pytest.mark.unit
@pytest.mark.asyncio
class TestMembershipService:
    """Verify authorized membership transitions and their side effects."""

    async def test_suspend_and_resume_retains_role_and_audits_both(self) -> None:
        """Pause access, revoke sessions, and restore the retained role."""
        service, uow, actor, target, now = _fixture()

        suspended = await service.suspend(
            actor_user_id=actor.user_id,
            organization_id=target.organization_id,
            membership_id=target.id,
        )
        resumed = await service.resume(
            actor_user_id=actor.user_id,
            organization_id=target.organization_id,
            membership_id=target.id,
        )

        assert suspended.status == 'suspended'
        assert resumed.status == 'active'
        assert resumed.role == target.role
        assert uow.sessions.revocations == [(target.user_id, target.organization_id, now)]
        assert [event[2] for event in uow.audit_events.actions] == [
            'membership.suspend',
            'membership.resume',
        ]
        assert uow.commit_count == 2

    async def test_revocation_requires_explicit_regrant_with_role(self) -> None:
        """Require a new role selection after revocation of the existing row."""
        service, uow, actor, target, now = _fixture()
        revoked = await service.revoke(
            actor_user_id=actor.user_id,
            organization_id=target.organization_id,
            membership_id=target.id,
        )

        with pytest.raises(MembershipTransitionError):
            await service.resume(
                actor_user_id=actor.user_id,
                organization_id=target.organization_id,
                membership_id=target.id,
            )

        regranted = await service.regrant(
            actor_user_id=actor.user_id,
            organization_id=target.organization_id,
            membership_id=target.id,
            role=MembershipRole.DEAL_DESK,
        )

        assert revoked.status == 'revoked'
        assert regranted.id == target.id
        assert regranted.status == 'active'
        assert regranted.role == MembershipRole.DEAL_DESK
        assert uow.sessions.revocations == [(target.user_id, target.organization_id, now)]
        assert [event[2] for event in uow.audit_events.actions] == [
            'membership.revoke',
            'membership.regrant',
        ]
        assert uow.commit_count == 2
        assert uow.rollback_count == 1

    async def test_non_administrator_cannot_change_membership(self) -> None:
        """Reject an actor without an active administrator membership."""
        service, uow, actor, target, _ = _fixture(actor_role=MembershipRole.AUDITOR)

        with pytest.raises(MembershipPermissionDeniedError):
            await service.suspend(
                actor_user_id=actor.user_id,
                organization_id=target.organization_id,
                membership_id=target.id,
            )

        assert uow.memberships.items[target.id].status == 'active'
        assert uow.sessions.revocations == []
        assert uow.audit_events.actions == []
        assert uow.rollback_count == 1

    async def test_target_must_belong_to_actor_organization(self) -> None:
        """Hide memberships outside the administrator's organization."""
        service, uow, actor, target, _ = _fixture()
        other_organization_id = uuid4()
        uow.memberships.items[target.id] = replace(target, organization_id=other_organization_id)

        with pytest.raises(MembershipNotFoundError):
            await service.revoke(
                actor_user_id=actor.user_id,
                organization_id=actor.organization_id,
                membership_id=target.id,
            )

        assert uow.sessions.revocations == []
        assert uow.audit_events.actions == []
        assert uow.rollback_count == 1
