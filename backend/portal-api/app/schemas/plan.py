from typing import Literal

from pydantic import BaseModel, Field


class PlanMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    timestamp: str  # ISO 8601


class PlanItinerary(BaseModel):
    stops: list[dict] = []
    budget: int = 0
    vibe_chaos: int = Field(default=50, ge=0, le=100)
    vibe_hidden: int = Field(default=50, ge=0, le=100)


class PlanCreate(BaseModel):
    title: str = "New Plan"
    messages: list[PlanMessage] = []
    itinerary: PlanItinerary = Field(default_factory=PlanItinerary)


class PlanUpdate(BaseModel):
    title: str | None = None
    # Full replacement list — caller appends locally then pushes the full array
    messages: list[PlanMessage] | None = None
    itinerary: PlanItinerary | None = None


class PlanRead(BaseModel):
    plan_id: str
    user_id: str
    title: str
    messages: list[PlanMessage]
    itinerary: PlanItinerary
    created_at: str
    updated_at: str
