from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db
from app.models.saved_event import SavedEvent
from app.models.user import User
from app.schemas.saved_event import SavedEventCreate, SavedEventRead

router = APIRouter(prefix="/users/me/saved-events", tags=["saved-events"])


@router.get("", response_model=list[SavedEventRead])
async def list_saved_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[SavedEvent]:
    result = await db.execute(
        select(SavedEvent)
        .where(SavedEvent.user_id == current_user.id)
        .order_by(SavedEvent.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=SavedEventRead, status_code=status.HTTP_201_CREATED)
async def save_event(
    body: SavedEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SavedEvent:
    saved = SavedEvent(user_id=current_user.id, **body.model_dump())
    db.add(saved)
    try:
        await db.commit()
        await db.refresh(saved)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="El evento ya está guardado"
        )
    return saved


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unsave_event(
    event_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(SavedEvent).where(
            SavedEvent.user_id == current_user.id,
            SavedEvent.event_id == event_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Evento guardado no encontrado"
        )
    await db.commit()
