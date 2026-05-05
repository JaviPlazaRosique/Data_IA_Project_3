import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SavedEventCreate(BaseModel):
    event_id: str
    event_title: str | None = None
    event_venue: str | None = None
    event_date: str | None = None
    event_time: str | None = None
    event_image_url: str | None = None
    event_url: str | None = None


SwipeDirection = Literal["left", "right"]
RecommendationContext = Literal["swipe", "chat"]
SwipeSchemaVersion = Literal["2.0"]


class SwipeEventProducer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    surface: RecommendationContext
    client_version: str | None = None


class SwipeEventSnapshot(BaseModel):
    model_config = ConfigDict(extra="ignore")

    event_id: str
    segmento: str | None = None
    genero: str | None = None
    subgenero: str | None = None
    ciudad: str | None = None
    recinto_id: str | None = None
    fecha_evento: str | None = None
    precio_min: float | None = Field(default=None, ge=0)
    precio_max: float | None = Field(default=None, ge=0)
    banda_precio: str | None = None


class SwipeEventCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    schema_version: SwipeSchemaVersion | None = None
    event_id: str
    direction: SwipeDirection
    swiped_at: datetime | None = None
    dwell_ms: int | None = Field(default=None, ge=0)
    session_id: str | None = None
    recommendation_context: RecommendationContext | None = None
    rank_position: int | None = Field(default=None, ge=0)
    recommendation_id: str | None = None
    producer: SwipeEventProducer | None = None
    event_snapshot: SwipeEventSnapshot | None = None


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
