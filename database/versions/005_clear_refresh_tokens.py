"""invalidate all plain-text refresh tokens

Revision ID: 005
Revises: 004
Create Date: 2026-04-11

Refresh tokens are now stored as SHA-256 hashes. Any existing plain-text tokens
in the database are unusable with the new comparison logic and must be cleared.
All active sessions will require a fresh login after this migration runs.
"""
from alembic import op

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Clear all existing refresh tokens — they are plain-text and incompatible
    # with the new hash-based storage. Users will be prompted to log in again.
    op.execute("UPDATE users SET refresh_token = NULL, refresh_token_expires_at = NULL")


def downgrade() -> None:
    # Tokens cannot be restored (they were never stored in reversible form).
    # Downgrade just clears again to leave the column in a consistent state.
    op.execute("UPDATE users SET refresh_token = NULL, refresh_token_expires_at = NULL")
