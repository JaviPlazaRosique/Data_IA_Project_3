import re
import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


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
    username: str | None = None
    full_name: str | None = None
    avatar_url: str | None = None
    preferred_budget: str | None = None
    preferred_location: str | None = None
    preferred_location_lat: float | None = None
    preferred_location_lng: float | None = None
    preferred_categories: list[str] | None = None

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{2,29}$", v):
            raise ValueError(
                "El nombre de usuario debe tener entre 3 y 30 caracteres y solo puede "
                "contener letras, números, guiones bajos (_) y guiones (-)."
            )
        return v
