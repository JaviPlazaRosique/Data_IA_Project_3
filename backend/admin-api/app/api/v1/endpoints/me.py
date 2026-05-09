import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.auth.dependencies import get_admin_user
from app.models.user import User

router = APIRouter(prefix="/me", tags=["me"])


class AdminUserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None
    is_active: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("", response_model=AdminUserRead)
async def get_me(user: User = Depends(get_admin_user)) -> AdminUserRead:
    return AdminUserRead.model_validate(user)
