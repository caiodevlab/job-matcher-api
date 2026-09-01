"""initial schema: jobs table

Revision ID: 001
Revises:
Create Date: 2026-09-01
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("location", sa.String(length=200), nullable=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="unknown"),
        sa.Column("source_hash", sa.String(length=64), nullable=False),
        sa.Column("level", sa.String(length=50), nullable=True),
        sa.Column("scraped_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_hash", name="uq_jobs_source_hash"),
    )
    op.create_index("ix_jobs_title", "jobs", ["title"])
    op.create_index("ix_jobs_source_hash", "jobs", ["source_hash"])


def downgrade() -> None:
    op.drop_index("ix_jobs_source_hash", table_name="jobs")
    op.drop_index("ix_jobs_title", table_name="jobs")
    op.drop_table("jobs")
