"""SQLAlchemy user repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from enact.identity.entities import User
from enact.identity.errors import UserEmailAlreadyExistsError, UserNotFoundError

from ..models.identity import User as UserModel
from ..session.flush import flush_session

_CONSTRAINT_ERRORS = {'uq_users_email': UserEmailAlreadyExistsError}


class SqlAlchemyUserRepository:
    """Persist and retrieve users through an asynchronous SQLAlchemy session."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository.

        Args:
            session: Session used for queries and mutations.
        """
        self._session = session

    async def get(self, user_id: UUID) -> User | None:
        """Return one user by identifier.

        Args:
            user_id: User identifier to look up.

        Returns:
            The matching user, or ``None`` when it does not exist.
        """
        model = await self._session.get(UserModel, user_id)
        return to_user(model) if model is not None else None

    async def find_by_email(self, email: str) -> User | None:
        """Find one user by normalized email address.

        Args:
            email: Canonical email address to look up.

        Returns:
            The matching user, or ``None`` when it does not exist.
        """
        model = await self._session.scalar(select(UserModel).where(UserModel.email == email))
        return to_user(model) if model is not None else None

    async def create(
        self,
        *,
        email: str,
        password_hash: str,
        display_name: str,
    ) -> User:
        """Create a user identity.

        Args:
            email: Canonical email address for the user.
            password_hash: Password hash for persistent storage.
            display_name: Name shown for the user.

        Returns:
            The created user.
        """
        model = UserModel(email=email, password_hash=password_hash, display_name=display_name)
        self._session.add(model)
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)
        return to_user(model)

    async def update_profile(
        self,
        user_id: UUID,
        *,
        email: str,
        display_name: str,
    ) -> User:
        """Update editable user profile fields.

        Args:
            user_id: User identifier to update.
            email: Canonical replacement email address.
            display_name: Replacement display name.

        Returns:
            The updated user.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        model = await self._session.get(UserModel, user_id)

        if model is None:
            raise UserNotFoundError(user_id)

        model.email = email
        model.display_name = display_name
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)

        return to_user(model)

    async def disable(self, user_id: UUID) -> None:
        """Disable a user without deleting its audit history.

        Args:
            user_id: User identifier to disable.

        Raises:
            UserNotFoundError: If the user does not exist.
        """
        model = await self._session.get(UserModel, user_id)

        if model is None:
            raise UserNotFoundError(user_id)

        model.status = 'disabled'
        await flush_session(self._session, constraint_errors=_CONSTRAINT_ERRORS)


def to_user(model: UserModel) -> User:
    return User(
        id=model.id,
        email=model.email,
        password_hash=model.password_hash,
        display_name=model.display_name,
        status=model.status,
    )
