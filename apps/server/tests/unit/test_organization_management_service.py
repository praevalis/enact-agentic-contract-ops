"""Unit tests for administrator organization profile changes."""

from dataclasses import replace
from datetime import datetime
from types import TracebackType
from typing import cast
from uuid import UUID, uuid4

import pytest
from enact.identity.entities import Membership, Organization
from enact.identity.errors import MembershipPermissionDeniedError
from enact.identity.services import OrganizationManagementService
from enact.identity.unit_of_work import IdentityUnitOfWork


class _Memberships:
    def __init__(self, membership: Membership) -> None:
        self.membership = membership

    async def get_for_user_and_organization(
        self, user_id: UUID, organization_id: UUID
    ) -> Membership | None:
        if (
            self.membership.user_id == user_id
            and self.membership.organization_id == organization_id
        ):
            return self.membership
        return None


class _Organizations:
    def __init__(self, organization: Organization) -> None:
        self.organization = organization
        self.updates: list[str] = []

    async def get(self, organization_id: UUID) -> Organization | None:
        return self.organization if self.organization.id == organization_id else None

    async def update_profile(self, organization_id: UUID, *, name: str) -> Organization:
        assert organization_id == self.organization.id
        self.organization = replace(self.organization, name=name)
        self.updates.append(name)
        return self.organization


class _AuditEvents:
    def __init__(self) -> None:
        self.actions: list[str] = []

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
        assert organization_id == resource_id
        assert resource_type == 'organization'
        assert details is not None
        self.actions.append(action)


class _UnitOfWork:
    def __init__(self, organization: Organization, membership: Membership) -> None:
        self.organizations = _Organizations(organization)
        self.memberships = _Memberships(membership)
        self.audit_events = _AuditEvents()
        self.organization_context: UUID | None = None

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
        pass


@pytest.mark.unit
@pytest.mark.asyncio
class TestOrganizationManagementService:
    """Verify rename authorization and atomic audit behavior."""

    async def test_administrator_renames_organization_and_audits_change(self) -> None:
        """Persist one profile change under the selected tenant context."""
        organization = Organization(uuid4(), 'Acme Cloud', 'active')
        actor = Membership(uuid4(), uuid4(), organization.id, 'administrator', 'active')
        uow = _UnitOfWork(organization, actor)
        service = OrganizationManagementService(uow=cast(IdentityUnitOfWork, uow))

        updated = await service.rename(
            actor_user_id=actor.user_id, organization_id=organization.id, name='Acme Operations'
        )

        assert updated.name == 'Acme Operations'
        assert uow.organization_context == organization.id
        assert uow.organizations.updates == ['Acme Operations']
        assert uow.audit_events.actions == ['organization.rename']

    async def test_non_administrator_and_other_tenant_cannot_rename(self) -> None:
        """Reject unauthorized writes without changing the profile or audit log."""
        organization = Organization(uuid4(), 'Acme Cloud', 'active')
        actor = Membership(uuid4(), uuid4(), organization.id, 'auditor', 'active')
        uow = _UnitOfWork(organization, actor)
        service = OrganizationManagementService(uow=cast(IdentityUnitOfWork, uow))

        with pytest.raises(MembershipPermissionDeniedError):
            await service.rename(
                actor_user_id=actor.user_id, organization_id=organization.id, name='Wrong'
            )

        with pytest.raises(MembershipPermissionDeniedError):
            await service.rename(actor_user_id=actor.user_id, organization_id=uuid4(), name='Wrong')

        assert uow.organizations.updates == []
        assert uow.audit_events.actions == []
