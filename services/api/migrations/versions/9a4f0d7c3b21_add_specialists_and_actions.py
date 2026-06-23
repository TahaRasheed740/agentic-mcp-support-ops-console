"""add specialists and approval actions

Revision ID: 9a4f0d7c3b21
Revises: 4f6cd88a0b72
Create Date: 2026-06-23
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9a4f0d7c3b21"
down_revision: str | Sequence[str] | None = "4f6cd88a0b72"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigation_specialist_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), nullable=False),
        sa.Column("specialist", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("findings", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("proposed_actions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investigation_id", "specialist"),
    )
    op.create_index(
        "ix_investigation_specialist_reports_investigation_id",
        "investigation_specialist_reports",
        ["investigation_id"],
    )
    op.create_table(
        "investigation_proposed_actions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("investigation_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=60), nullable=False),
        sa.Column("service", sa.String(length=30), nullable=False),
        sa.Column("tool_name", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("arguments", sa.JSON(), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("idempotency_key", sa.String(length=100), nullable=False),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_investigation_proposed_actions_investigation_id",
        "investigation_proposed_actions",
        ["investigation_id"],
    )
    op.create_index(
        "ix_investigation_proposed_actions_status",
        "investigation_proposed_actions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_investigation_proposed_actions_status", table_name="investigation_proposed_actions")
    op.drop_index(
        "ix_investigation_proposed_actions_investigation_id",
        table_name="investigation_proposed_actions",
    )
    op.drop_table("investigation_proposed_actions")
    op.drop_index(
        "ix_investigation_specialist_reports_investigation_id",
        table_name="investigation_specialist_reports",
    )
    op.drop_table("investigation_specialist_reports")
