"""add event_url to saved_events

Revision ID: 009
Revises: 008
Create Date: 2026-04-23

Stores the ticketing URL snapshot alongside other event metadata so the
saved-events card in the profile can link directly to the seller without
a round-trip to Firestore.
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "saved_events",
        sa.Column("event_url", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("saved_events", "event_url")
