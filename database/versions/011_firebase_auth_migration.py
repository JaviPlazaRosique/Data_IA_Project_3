"""switch users table to firebase auth

Revision ID: 011
Revises: 010
Create Date: 2026-04-29

Fresh start for auth: wipe existing users, drop password/refresh-token columns,
add firebase_uid. ON DELETE CASCADE on saved_events handles dependent rows.
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DELETE FROM users")

    op.add_column(
        "users",
        sa.Column("firebase_uid", sa.String(length=128), nullable=False),
    )
    op.create_unique_constraint("uq_users_firebase_uid", "users", ["firebase_uid"])

    op.drop_column("users", "hashed_password")
    op.drop_column("users", "refresh_token")
    op.drop_column("users", "refresh_token_expires_at")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("refresh_token_expires_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("users", sa.Column("refresh_token", sa.Text(), nullable=True))
    op.add_column(
        "users",
        sa.Column("hashed_password", sa.String(length=255), nullable=False, server_default=""),
    )
    op.drop_constraint("uq_users_firebase_uid", "users", type_="unique")
    op.drop_column("users", "firebase_uid")
