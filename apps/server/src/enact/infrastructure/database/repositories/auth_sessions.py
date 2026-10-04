"""SQLAlchemy authentication session repository implementation."""

from collections.abc import Sequence
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import AuthSession
from enact.identity.errors import AuthSessionAlreadyExistsError, AuthSessionNotFoundError

from ..models.auth import AuthSession as AuthSessionModel
from ..session.flush import flush_session

_CONSTRAINT_ERRORS = {'uq_auth_session_refresh_digest': AuthSessionAlreadyExistsError}


class SqlAlchemyAuthSessionRepository:
    """Persist authentication sessions through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def get(self, session_id: UUID) -> AuthSession | None:
        """Return one authentication session by identifier.

        Args:
            session_id: Session identifier to look up.

        Returns:
            The matching session, or ``None`` when it does not exist.
        """
        model = await self._session.get(AuthSessionModel, session_id)
        return to_auth_session(model) if model is not None else None

    async def create(
        self,
        *,
        user_id: UUID,
        organization_id: UUID,
        token_family_id: UUID,
        refresh_token_digest: str,
        expires_at: datetime,
    ) -> AuthSession:
        """Create an authentication session.

        Args:
            user_id: User owning the session.
            organization_id: Session's current organization.
            token_family_id: Token family identifier for reuse detection.
            refresh_token_digest: Deterministic digest of the current refresh token.
            expires_at: Session expiration timestamp.

        Returns:
            The created authentication session.
        """
        model = AuthSessionModel(
            user_id=user_id,
            current_organization_id=organization_id,
            token_family_id=token_family_id,
            refresh_token_digest=refresh_token_digest,
            expires_at=expires_at,
        )
        self._session.add(model)
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)
        return to_auth_session(model)

    async def find_by_token_digest(self, refresh_token_digest: str) -> AuthSession | None:
        """Find a session by its deterministic refresh-token digest.

        Args:
            refresh_token_digest: Digest of the refresh token to look up.

        Returns:
            The matching session, or ``None`` when it does not exist.
        """
        model = await self._session.scalar(
            select(AuthSessionModel).where(
                AuthSessionModel.refresh_token_digest == refresh_token_digest
            )
        )
        return to_auth_session(model) if model is not None else None

    async def rotate(
        self,
        session_id: UUID,
        replacement_session_id: UUID,
        used_at: datetime,
    ) -> None:
        """Revoke a session and link it to its replacement.

        Args:
            session_id: Session whose refresh token was used.
            replacement_session_id: Newly created replacement session.
            used_at: Timestamp when the refresh token was used.

        Raises:
            AuthSessionNotFoundError: If the session does not exist.
        """
        model = await self._session.get(AuthSessionModel, session_id)

        if model is None:
            raise AuthSessionNotFoundError(session_id)

        model.last_used_at = used_at
        model.revoked_at = used_at
        model.replaced_by_session_id = replacement_session_id
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

    async def revoke(self, session_id: UUID, revoked_at: datetime) -> None:
        """Revoke one authentication session.

        Args:
            session_id: Session identifier to revoke.
            revoked_at: Timestamp of revocation.

        Raises:
            AuthSessionNotFoundError: If the session does not exist.
        """
        model = await self._session.get(AuthSessionModel, session_id)

        if model is None:
            raise AuthSessionNotFoundError(session_id)

        model.revoked_at = revoked_at
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

    async def revoke_family(self, token_family_id: UUID, revoked_at: datetime) -> None:
        """Revoke every session in a token family.

        Args:
            token_family_id: Token family whose sessions should be revoked.
            revoked_at: Timestamp of revocation.
        """
        await self._session.execute(
            update(AuthSessionModel)
            .where(
                AuthSessionModel.token_family_id == token_family_id,
                AuthSessionModel.revoked_at.is_(None),
            )
            .values(revoked_at=revoked_at)
        )
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

    async def list_active_for_user(self, user_id: UUID) -> Sequence[AuthSession]:
        """List active sessions for account-management operations.

        Args:
            user_id: User whose sessions should be listed.

        Returns:
            The user's non-revoked, non-expired authentication sessions.
        """
        result = await self._session.scalars(
            select(AuthSessionModel)
            .where(
                AuthSessionModel.user_id == user_id,
                AuthSessionModel.revoked_at.is_(None),
                AuthSessionModel.expires_at > func.now(),
            )
            .order_by(AuthSessionModel.created_at.desc())
        )
        return [to_auth_session(model) for model in result.all()]


def to_auth_session(model: AuthSessionModel) -> AuthSession:
    return AuthSession(
        id=model.id,
        user_id=model.user_id,
        current_organization_id=model.current_organization_id,
        token_family_id=model.token_family_id,
        refresh_token_digest=model.refresh_token_digest,
        expires_at=model.expires_at,
        last_used_at=model.last_used_at,
        revoked_at=model.revoked_at,
        replaced_by_session_id=model.replaced_by_session_id,
    )
