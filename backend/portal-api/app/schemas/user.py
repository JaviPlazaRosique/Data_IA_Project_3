import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    full_name: str | None = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must only contain letters, numbers, hyphens, and underscores")
        if len(v) < 3 or len(v) > 100:
            raise ValueError("Username must be between 3 and 100 characters")
        return v

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


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
    password: str | None = None

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str | None) -> str | None:
        if v is not None and len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
