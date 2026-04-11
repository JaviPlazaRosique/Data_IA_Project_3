"""clean up user indexes and add soft-delete partial index

Revision ID: 004
Revises: 003
Create Date: 2026-04-11

1. Drop idx_users_email and idx_users_username — both columns already have a
   UNIQUE constraint, which PostgreSQL implements as a unique index. The
   additional plain (non-unique) indexes are redundant.

2. Add idx_users_active_email — a partial index covering only active users
   (is_active = TRUE). Login and registration duplicate-checks filter on
   is_active, so this index is much smaller than a full-table scan and avoids
   touching soft-deleted rows.
"""
import sqlalchemy as sa
from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_username", table_name="users")

    # Partial index for login / register queries — only active users
    op.create_index(
        "idx_users_active_email",
        "users",
        ["email"],
        postgresql_where=sa.text("is_active = TRUE"),
    )


def downgrade() -> None:
    op.drop_index("idx_users_active_email", table_name="users")
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_username", "users", ["username"])
