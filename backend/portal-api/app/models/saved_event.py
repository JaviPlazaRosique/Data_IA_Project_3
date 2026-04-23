import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SavedEvent(Base):
    __tablename__ = "saved_events"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_saved_events_user_event"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_id: Mapped[str] = mapped_column(Text, nullable=False)
    event_title: Mapped[str | None] = mapped_column(Text)
    event_venue: Mapped[str | None] = mapped_column(Text)
    event_date: Mapped[str | None] = mapped_column(Text)
    event_time: Mapped[str | None] = mapped_column(Text)
    event_image_url: Mapped[str | None] = mapped_column(Text)
    event_url: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
