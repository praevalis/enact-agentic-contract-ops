"""Allow each amendment case to have only one predecessor."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = '0006_unique_amendment_predecessor'
down_revision: str | None = '0005_organization_onboarding'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = 'enact'
INDEX = 'uq_case_lineage_amends_target'


def upgrade() -> None:
    """Enforce one incoming amends edge per case within its organization."""
    op.create_index(
        INDEX,
        'case_lineage',
        ['organization_id', 'target_case_id'],
        unique=True,
        schema=SCHEMA,
        postgresql_where=sa.text("relationship_type = 'amends'"),
    )


def downgrade() -> None:
    """Permit multiple incoming amends edges again."""
    op.drop_index(INDEX, table_name='case_lineage', schema=SCHEMA)
