"""reconcile missing columns from 006/008/009

Revision ID: 010
Revises: 009
Create Date: 2026-04-24

Heals databases that were stamped at 009 (e.g. via schema.sql) but predate
migrations 006/008/009 and therefore lack the columns those migrations added.
All ALTERs use IF NOT EXISTS so this is a no-op on fully-migrated databases.
"""
from alembic import op

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE users "
        "ADD COLUMN IF NOT EXISTS preferred_location_lat DOUBLE PRECISION, "
        "ADD COLUMN IF NOT EXISTS preferred_location_lng DOUBLE PRECISION, "
        "ADD COLUMN IF NOT EXISTS preferred_categories   TEXT[]"
    )
    op.execute(
        "ALTER TABLE saved_events "
        "ADD COLUMN IF NOT EXISTS event_url TEXT"
    )


def downgrade() -> None:
    # No-op: downgrading would destroy data added by 006/008/009.
    pass
