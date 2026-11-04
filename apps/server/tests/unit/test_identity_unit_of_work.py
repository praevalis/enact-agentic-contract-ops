"""Unit tests for the identity unit-of-work boundary."""

from typing import cast

import pytest
from enact.infrastructure.database.uows import SqlAlchemyIdentityUnitOfWork
from sqlalchemy.ext.asyncio import AsyncSession


class _Session:
    """Record transaction operations for unit-of-work tests."""

    def __init__(self, *, commit_error: BaseException | None = None) -> None:
        """Initialize the recording session.

        Args:
            commit_error: Optional error raised during commit.
        """
        self.commit_error = commit_error
        self.commit_count = 0
        self.rollback_count = 0

    async def commit(self) -> None:
        """Record or fail the commit operation."""
        self.commit_count += 1
        if self.commit_error is not None:
            raise self.commit_error

    async def rollback(self) -> None:
        """Record the rollback operation."""
        self.rollback_count += 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestSqlAlchemyIdentityUnitOfWork:
    """Verify identity transaction ownership."""

    async def test_commits_when_scope_succeeds(self) -> None:
        """Commit one transaction after a successful workflow."""
        session = _Session()
        unit_of_work = SqlAlchemyIdentityUnitOfWork(cast(AsyncSession, session))

        async with unit_of_work:
            pass

        assert session.commit_count == 1
        assert session.rollback_count == 0

    async def test_rolls_back_when_scope_raises(self) -> None:
        """Roll back and preserve the original workflow exception."""
        session = _Session()
        unit_of_work = SqlAlchemyIdentityUnitOfWork(cast(AsyncSession, session))

        with pytest.raises(RuntimeError, match='workflow failed'):
            async with unit_of_work:
                raise RuntimeError('workflow failed')

        assert session.commit_count == 0
        assert session.rollback_count == 1

    async def test_rolls_back_when_commit_fails(self) -> None:
        """Roll back when the transaction cannot commit."""
        session = _Session(commit_error=RuntimeError('commit failed'))
        unit_of_work = SqlAlchemyIdentityUnitOfWork(cast(AsyncSession, session))

        with pytest.raises(RuntimeError, match='commit failed'):
            async with unit_of_work:
                pass

        assert session.commit_count == 1
        assert session.rollback_count == 1
