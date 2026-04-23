"""add preferred_categories to users

Revision ID: 008
Revises: 007
Create Date: 2026-04-23

Stores the user's favorite event categories (multi-select). Mirrors the
segmento values surfaced in the map filter.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("preferred_categories", postgresql.ARRAY(sa.Text()), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "preferred_categories")
