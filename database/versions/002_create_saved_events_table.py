"""create saved_events table

Revision ID: 002
Revises: 001
Create Date: 2026-04-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "saved_events",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_id", sa.Text(), nullable=False),
        sa.Column("event_title", sa.Text(), nullable=True),
        sa.Column("event_venue", sa.Text(), nullable=True),
        sa.Column("event_date", sa.Text(), nullable=True),
        sa.Column("event_time", sa.Text(), nullable=True),
        sa.Column("event_image_url", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_unique_constraint(
        "uq_saved_events_user_event", "saved_events", ["user_id", "event_id"]
    )
    op.create_index("idx_saved_events_user_id", "saved_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("idx_saved_events_user_id", table_name="saved_events")
    op.drop_constraint("uq_saved_events_user_event", "saved_events", type_="unique")
    op.drop_table("saved_events")
