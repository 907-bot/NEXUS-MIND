"""Initial schema: sessions, tasks, agent_outputs

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── sessions ─────────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("user_id", sa.String(), nullable=False, index=True),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, default="initialized"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── tasks ─────────────────────────────────────────────────────────────────
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(),
                  sa.ForeignKey("sessions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("skill_tag", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, default="pending"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── agent_outputs ─────────────────────────────────────────────────────────
    op.create_table(
        "agent_outputs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("session_id", sa.String(),
                  sa.ForeignKey("sessions.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("task_id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("skill_tag", sa.String(), nullable=False),
        sa.Column("output", sa.JSON(), nullable=True),
        sa.Column("quality_score", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_outputs")
    op.drop_table("tasks")
    op.drop_table("sessions")
