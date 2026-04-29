import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None
    avatar_url: str | None
    is_active: bool
    is_verified: bool
    preferred_budget: str | None
    preferred_location: str | None
    preferred_location_lat: float | None
    preferred_location_lng: float | None
    preferred_categories: list[str] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    preferred_budget: str | None = None
    preferred_location: str | None = None
    preferred_location_lat: float | None = None
    preferred_location_lng: float | None = None
    preferred_categories: list[str] | None = None
