"""add preferred_location_lat and preferred_location_lng to users

Revision ID: 006
Revises: 005
Create Date: 2026-04-19

Stores the resolved coordinates for the user's preferred city (picked from the
profile autocomplete). With lat/lng persisted the map can center without any
runtime geocoding, and ambiguous names (Valencia ES vs Valencia VE) resolve
once — at the moment the user selects from the suggestion list.
"""
from alembic import op
import sqlalchemy as sa

revision = "006"
down_revision = "005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("preferred_location_lat", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("preferred_location_lng", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "preferred_location_lng")
    op.drop_column("users", "preferred_location_lat")
