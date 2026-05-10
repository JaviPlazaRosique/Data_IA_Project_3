import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_db
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])


class UserAdminRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: str | None
    is_active: bool
    is_verified: bool
    is_admin: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAdminPatch(BaseModel):
    is_active: bool | None = None
    is_admin: bool | None = None


class UserAdminListResponse(BaseModel):
    items: list[UserAdminRead]
    total: int
    page: int
    limit: int


@router.get("", response_model=UserAdminListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    search: str | None = None,
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminListResponse:
    from sqlalchemy import func, or_

    q = select(User)
    count_q = select(func.count()).select_from(User)

    if search:
        pattern = f"%{search}%"
        filt = or_(User.email.ilike(pattern), User.username.ilike(pattern))
        q = q.where(filt)
        count_q = count_q.where(filt)

    total = (await db.execute(count_q)).scalar_one()
    offset = (page - 1) * limit
    users = (await db.execute(q.order_by(User.created_at.desc()).offset(offset).limit(limit))).scalars().all()

    return UserAdminListResponse(
        items=[UserAdminRead.model_validate(u) for u in users],
        total=total,
        page=page,
        limit=limit,
    )


@router.patch("/{user_id}", response_model=UserAdminRead)
async def patch_user(
    user_id: uuid.UUID,
    patch: UserAdminPatch,
    admin: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserAdminRead:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if patch.is_active is not None:
        user.is_active = patch.is_active
    if patch.is_admin is not None:
        if user.id == admin.id and not patch.is_admin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove your own admin role",
            )
        user.is_admin = patch.is_admin

    await db.commit()
    await db.refresh(user)
    return UserAdminRead.model_validate(user)
