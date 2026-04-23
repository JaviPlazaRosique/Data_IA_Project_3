from fastapi import APIRouter, Body, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.firestore import get_firestore
from app.dependencies import get_current_user, get_db
from app.models.saved_event import SavedEvent
from app.models.user import User
from app.schemas.saved_event import SavedEventRead
from app.schemas.user import UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserRead)
async def update_me(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    update_data = body.model_dump(exclude_unset=True)

    if "password" in update_data:
        current_user.hashed_password = hash_password(update_data.pop("password"))

    for field, value in update_data.items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete (deactivate) the account. Data is retained. Use /me/data for full erasure."""
    current_user.is_active = False
    current_user.refresh_token = None
    current_user.refresh_token_expires_at = None
    await db.commit()


@router.delete("/me/data", status_code=status.HTTP_204_NO_CONTENT)
async def erase_me(
    confirm: str = Body(..., embed=True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """GDPR Art. 17 — permanent erasure of all personal data.

    Requires body: {"confirm": "DELETE MY ACCOUNT"}
    Deletes: Firestore plans, saved_events, and the user row.
    ON DELETE CASCADE handles child table rows automatically.
    """
    if confirm != "DELETE MY ACCOUNT":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Send {"confirm": "DELETE MY ACCOUNT"} to confirm erasure.',
        )

    # Delete Firestore plans belonging to this user
    firestore = get_firestore()
    plans_query = firestore.collection("plans").where(
        "user_id", "==", str(current_user.id)
    )
    plan_docs = await plans_query.get()
    for doc in plan_docs:
        await doc.reference.delete()

    # Hard-delete the user row; ON DELETE CASCADE removes saved_events
    await db.delete(current_user)
    await db.commit()


@router.get("/me/export")
async def export_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    """GDPR Art. 15 / Art. 20 — data access and portability.

    Returns a JSON file containing all personal data held for the authenticated user.
    """
    import json

    saved_result = await db.execute(
        select(SavedEvent).where(SavedEvent.user_id == current_user.id)
    )

    saved_events = [
        SavedEventRead.model_validate(e).model_dump(mode="json")
        for e in saved_result.scalars().all()
    ]

    profile = UserRead.model_validate(current_user).model_dump(mode="json")

    export_data = {
        "profile": profile,
        "saved_events": saved_events,
        "plans_note": "Your AI planning conversations are available at GET /api/v1/plans",
    }

    content = json.dumps(export_data, indent=2, default=str)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="my-data.json"'},
    )
