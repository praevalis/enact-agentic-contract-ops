"""SQLAlchemy audit event repository implementation."""

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..models.audit import AuditEvent
from ..session.flush import flush_session


class SqlAlchemyAuditEventRepository:
    """Append organization audit events through an asynchronous session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the audit repository.

        Args:
            session: Session used for writes.
        """
        self._session = session

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
        self._session.add(
            AuditEvent(
                organization_id=organization_id,
                actor_user_id=actor_user_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                occurred_at=occurred_at,
                details=details,
            )
        )

        await flush_session(self._session)
