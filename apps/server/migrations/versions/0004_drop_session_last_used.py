"""Remove the misleading authentication-session last-used timestamp.

Upgrade discards historical values. Downgrade restores the nullable column, but cannot
recover those values.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0004_drop_session_last_used'
down_revision: str | None = '0003_membership_discovery'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'


def upgrade() -> None:
    """Remove the redundant session timestamp."""
    op.drop_column('auth_sessions', 'last_used_at', schema=SCHEMA)


def downgrade() -> None:
    """Restore the nullable session timestamp without historical values."""
    op.add_column(
        'auth_sessions',
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA,
    )
