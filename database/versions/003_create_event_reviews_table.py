"""create event_reviews table

Revision ID: 003
Revises: 002
Create Date: 2026-04-11
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_reviews",
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
        sa.Column("rating", sa.SmallInteger(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_unique_constraint(
        "uq_event_reviews_user_event", "event_reviews", ["user_id", "event_id"]
    )
    # Covering index: supports WHERE event_id = ? ORDER BY created_at DESC without a sort step
    op.create_index(
        "idx_event_reviews_event_id_created_at",
        "event_reviews",
        ["event_id", sa.text("created_at DESC")],
    )
    op.create_index("idx_event_reviews_user_id", "event_reviews", ["user_id"])
    op.create_check_constraint(
        "ck_event_reviews_rating", "event_reviews", "rating BETWEEN 1 AND 5"
    )


def downgrade() -> None:
    op.drop_constraint("ck_event_reviews_rating", "event_reviews", type_="check")
    op.drop_index("idx_event_reviews_user_id", table_name="event_reviews")
    op.drop_index("idx_event_reviews_event_id_created_at", table_name="event_reviews")
    op.drop_constraint("uq_event_reviews_user_event", "event_reviews", type_="unique")
    op.drop_table("event_reviews")
