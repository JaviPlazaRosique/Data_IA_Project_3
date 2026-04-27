import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class SavedEventCreate(BaseModel):
    event_id: str
    event_title: str | None = None
    event_venue: str | None = None
    event_date: str | None = None
    event_time: str | None = None
    event_image_url: str | None = None
    event_url: str | None = None


SwipeDirection = Literal["left", "right"]


class SwipeEventCreate(BaseModel):
    event_id: str
    direction: SwipeDirection
    swiped_at: datetime | None = None
    dwell_ms: int | None = Field(default=None, ge=0)


class SwipeEventAccepted(BaseModel):
    accepted: bool


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
