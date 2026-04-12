import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EventReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    review_text: str | None = None


class EventReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    review_text: str | None = None


class EventReviewRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    event_id: str
    rating: int
    review_text: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
