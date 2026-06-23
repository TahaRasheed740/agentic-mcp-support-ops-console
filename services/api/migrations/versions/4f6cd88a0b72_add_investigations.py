"""add investigations

Revision ID: 4f6cd88a0b72
Revises: c5a8d6b410ef
Create Date: 2026-06-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4f6cd88a0b72"
down_revision: str | Sequence[str] | None = "c5a8d6b410ef"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("case_id", sa.String(length=30), nullable=False),
        sa.Column("session_id", sa.String(length=36), nullable=True),
        sa.Column("persona_id", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("router_model", sa.String(length=100), nullable=False),
        sa.Column("investigator_model", sa.String(length=100), nullable=False),
        sa.Column("classification", sa.JSON(), nullable=True),
        sa.Column("plan", sa.JSON(), nullable=True),
        sa.Column("diagnosis", sa.JSON(), nullable=True),
        sa.Column("drafted_response", sa.Text(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_read_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cache_creation_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tool_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["case_id"], ["tickets.id"]),
        sa.ForeignKeyConstraint(["persona_id"], ["support_personas.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["demo_sessions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_investigations_case_id", "investigations", ["case_id"])
    op.create_index("ix_investigations_session_id", "investigations", ["session_id"])
    op.create_index("ix_investigations_status", "investigations", ["status"])
    op.create_table(
        "investigation_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_type", sa.String(length=60), nullable=False),
        sa.Column("agent", sa.String(length=60), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investigation_id", "sequence"),
    )
    op.create_index("ix_investigation_events_event_type", "investigation_events", ["event_type"])
    op.create_index("ix_investigation_events_investigation_id", "investigation_events", ["investigation_id"])
    op.create_table(
        "investigation_evidence",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), nullable=False),
        sa.Column("citation_id", sa.String(length=20), nullable=False),
        sa.Column("document_id", sa.String(length=120), nullable=False),
        sa.Column("chunk_id", sa.String(length=160), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("source_path", sa.String(length=500), nullable=False),
        sa.Column("excerpt", sa.Text(), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["investigation_id"], ["investigations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("investigation_id", "citation_id"),
        sa.UniqueConstraint("investigation_id", "chunk_id"),
    )
    op.create_index("ix_investigation_evidence_investigation_id", "investigation_evidence", ["investigation_id"])


def downgrade() -> None:
    op.drop_index("ix_investigation_evidence_investigation_id", table_name="investigation_evidence")
    op.drop_table("investigation_evidence")
    op.drop_index("ix_investigation_events_investigation_id", table_name="investigation_events")
    op.drop_index("ix_investigation_events_event_type", table_name="investigation_events")
    op.drop_table("investigation_events")
    op.drop_index("ix_investigations_status", table_name="investigations")
    op.drop_index("ix_investigations_session_id", table_name="investigations")
    op.drop_index("ix_investigations_case_id", table_name="investigations")
    op.drop_table("investigations")
