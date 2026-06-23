"""Create the foundation metadata table and enable vector support."""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260622_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "app_metadata",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=500), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.bulk_insert(
        sa.table(
            "app_metadata",
            sa.column("key", sa.String),
            sa.column("value", sa.String),
        ),
        [{"key": "schema_version", "value": revision}],
    )


def downgrade() -> None:
    op.drop_table("app_metadata")
