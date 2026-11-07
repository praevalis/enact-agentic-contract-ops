"""Shared fixtures for case and customer unit tests."""

from collections.abc import Callable, Sequence
from datetime import UTC, datetime, timedelta
from types import TracebackType
from uuid import UUID, uuid4

import pytest
from enact.cases.entities import Case, CaseCursor
from enact.customers.entities import Customer, CustomerCursor
from enact.identity.authentication import Principal

NOW = datetime(2026, 11, 5, tzinfo=UTC)


class _Customers:
    def __init__(self) -> None:
        self.items: dict[UUID, Customer] = {}

    async def create(self, *, organization_id: UUID, display_name: str) -> Customer:
        customer = Customer(uuid4(), organization_id, display_name, 'active', NOW, NOW)
        self.items[customer.id] = customer
        return customer

    async def get(self, customer_id: UUID) -> Customer | None:
        return self.items.get(customer_id)

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor: CustomerCursor | None = None,
        status: str | None = None,
        name_query: str | None = None,
    ) -> Sequence[Customer]:
        items = sorted(
            (
                customer
                for customer in self.items.values()
                if customer.organization_id == organization_id
            ),
            key=lambda customer: (customer.created_at, customer.id),
            reverse=True,
        )
        if cursor is not None:
            items = [
                customer
                for customer in items
                if (customer.created_at, customer.id) < (cursor.created_at, cursor.id)
            ]
        if status is not None:
            items = [customer for customer in items if customer.status == status]
        if name_query is not None:
            items = [
                customer
                for customer in items
                if name_query.lower() in customer.display_name.lower()
            ]
        return items[:limit]


class _Cases:
    def __init__(self) -> None:
        self.items: dict[UUID, Case] = {}

    async def create(
        self, *, organization_id: UUID, customer_id: UUID, title: str, case_type: str
    ) -> Case:
        case = Case(uuid4(), organization_id, customer_id, title, case_type, 'draft', 1, NOW, NOW)
        self.items[case.id] = case
        return case

    async def get(self, case_id: UUID) -> Case | None:
        return self.items.get(case_id)

    async def list_for_organization(
        self,
        *,
        organization_id: UUID,
        limit: int,
        cursor: CaseCursor | None = None,
        customer_id: UUID | None = None,
        case_type: str | None = None,
        status: str | None = None,
    ) -> Sequence[Case]:
        items = sorted(
            (case for case in self.items.values() if case.organization_id == organization_id),
            key=lambda case: (case.created_at, case.id),
            reverse=True,
        )
        if cursor is not None:
            items = [
                case
                for case in items
                if (case.created_at, case.id) < (cursor.created_at, cursor.id)
            ]
        if customer_id is not None:
            items = [case for case in items if case.customer_id == customer_id]
        if case_type is not None:
            items = [case for case in items if case.case_type == case_type]
        if status is not None:
            items = [case for case in items if case.status == status]
        return items[:limit]


class _Lineage:
    def __init__(self) -> None:
        self.edges: list[tuple[UUID, UUID, UUID]] = []

    async def create_amends(
        self, *, organization_id: UUID, source_case_id: UUID, target_case_id: UUID
    ) -> None:
        self.edges.append((organization_id, source_case_id, target_case_id))


class _Audit:
    def __init__(self) -> None:
        self.actions: list[tuple[str, UUID]] = []

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
        assert (
            organization_id
            and actor_user_id
            and resource_type
            and occurred_at
            and details is not None
        )
        self.actions.append((action, resource_id))


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.customers = _Customers()
        self.cases = _Cases()
        self.lineage = _Lineage()
        self.audit_events = _Audit()
        self.contexts: list[UUID] = []
        self.commits = 0
        self.rollbacks = 0

    async def set_organization_context(self, organization_id: UUID) -> None:
        self.contexts.append(organization_id)

    async def __aenter__(self) -> 'InMemoryUnitOfWork':
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc_type is None:
            await self.commit()
        else:
            await self.rollback()

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:
        self.rollbacks += 1


def make_principal(role: str = 'deal_desk') -> Principal:
    return Principal(
        user_id=uuid4(),
        organization_id=uuid4(),
        membership_id=uuid4(),
        role=role,
        session_id=uuid4(),
        access_token_expires_at=NOW + timedelta(minutes=15),
    )


@pytest.fixture
def in_memory_uow() -> InMemoryUnitOfWork:
    """Provide a fresh in-memory transaction boundary per test."""
    return InMemoryUnitOfWork()


@pytest.fixture
def principal_factory() -> Callable[[str], Principal]:
    """Provide principals with selectable organization roles."""
    return make_principal
