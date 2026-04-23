import uuid
from datetime import datetime

from pydantic import BaseModel


class SavedEventCreate(BaseModel):
    event_id: str
    event_title: str | None = None
    event_venue: str | None = None
    event_date: str | None = None
    event_time: str | None = None
    event_image_url: str | None = None
    event_url: str | None = None


class SavedEventRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: str
    event_title: str | None
    event_venue: str | None
    event_date: str | None
    event_time: str | None
    event_image_url: str | None
    event_url: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
