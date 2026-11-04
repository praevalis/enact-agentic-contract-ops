"""Audit event repository boundary."""

from datetime import datetime
from typing import Protocol
from uuid import UUID


class AuditEventRepository(Protocol):
    """Persist immutable records of organization actions."""

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
        """Record one organization action.

        Args:
            organization_id: Organization that owns the action.
            actor_user_id: User who performed the action.
            action: Stable action identifier.
            resource_type: Type of affected resource.
            resource_id: Identifier of the affected resource.
            occurred_at: Time of the action.
            details: Additional structured action details.
        """
        ...
