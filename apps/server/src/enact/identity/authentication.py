"""Authentication mechanisms and the authenticated request principal."""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import jwt
from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from .errors import InvalidAccessTokenError
from .schemas import AccessTokenClaims


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated user and organization context for one request."""

    user_id: UUID
    organization_id: UUID | None
    membership_id: UUID | None
    role: str | None
    session_id: UUID
    access_token_expires_at: datetime


class PasswordHasher:
    """Hash and verify user passwords with configured Argon2id parameters."""

    def __init__(self) -> None:
        """Initialize a password hasher with the configured Argon2id parameters."""
        self._hasher = Argon2Hasher()

    def hash(self, password: str) -> str:
        """Hash a plaintext password.

        Args:
            password: Plaintext password supplied by the user.

        Returns:
            A password hash suitable for persistent storage.
        """
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str) -> bool:
        """Verify a plaintext password against a stored hash.

        Args:
            password: Plaintext password supplied by the user.
            password_hash: Persisted password hash to verify against.

        Returns:
            ``True`` when the password matches; otherwise ``False``.
        """
        try:
            return self._hasher.verify(password_hash, password)
        except (InvalidHashError, VerificationError, VerifyMismatchError):
            return False

    def needs_rehash(self, password_hash: str) -> bool:
        """Check whether a stored hash uses outdated parameters.

        Args:
            password_hash: Persisted password hash to inspect.

        Returns:
            ``True`` when the hash should be regenerated with current parameters.
        """
        return self._hasher.check_needs_rehash(password_hash)


class AccessTokenCodec:
    """Encode and decode short-lived signed access tokens."""

    def __init__(self, secret_key: str, algorithm: str = 'HS256') -> None:
        """Initialize the codec.

        Args:
            secret_key: Key used to sign and verify access tokens.
            algorithm: JWT signing algorithm accepted during encoding and decoding.
        """
        self._secret_key = secret_key
        self._algorithm = algorithm

    def encode(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        organization_id: UUID | None,
        membership_id: UUID | None,
        role: str | None,
        expires_at: datetime,
    ) -> str:
        """Create a signed access token.

        Args:
            user_id: Authenticated user identifier.
            session_id: Authentication session identifier.
            organization_id: Active organization identifier.
            membership_id: Active organization membership identifier.
            role: Active membership role.
            expires_at: Token expiration timestamp.

        Returns:
            A signed serialized access token.
        """
        claims = {
            'sub': str(user_id),
            'sid': str(session_id),
            'org': str(organization_id) if organization_id is not None else None,
            'mid': str(membership_id) if membership_id is not None else None,
            'role': role,
            'exp': expires_at,
        }
        return jwt.encode(claims, self._secret_key, algorithm=self._algorithm)

    def decode(self, token: str) -> Principal:
        """Validate and decode an access token.

        Args:
            token: Signed serialized access token.

        Returns:
            The authenticated principal represented by the token.

        Raises:
            InvalidAccessTokenError: If the token signature, expiration, or claims are invalid.
        """
        try:
            raw_claims = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
        except jwt.InvalidTokenError as error:
            raise InvalidAccessTokenError('Invalid access token') from error

        try:
            claims = AccessTokenClaims.model_validate(raw_claims)
        except ValueError as error:
            raise InvalidAccessTokenError('Invalid access token claims') from error

        return Principal(
            user_id=claims.sub,
            session_id=claims.sid,
            organization_id=claims.org,
            membership_id=claims.mid,
            role=claims.role,
            access_token_expires_at=claims.exp,
        )
