import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_admin_user, get_db
from app.db.bigquery import bq_table, get_bq_client
from app.db.firestore import get_firestore
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stats", tags=["stats"])


class StatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_events: int
    total_saved_events: int
    total_swipes: int


def _count_swipes_sync() -> int:
    try:
        table = bq_table("recomendacion_planes", "fct_swipes")
        rows = get_bq_client().query(f"SELECT COUNT(*) as n FROM {table}").result()
        return next(iter(rows))["n"]
    except Exception:
        return -1


async def _count_events() -> int:
    try:
        db = get_firestore()
        docs = await db.collection("eventos").count().get()
        return docs[0][0].value
    except Exception:
        return -1


@router.get("", response_model=StatsResponse)
async def get_stats(
    _: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
) -> StatsResponse:
    total_users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    active_users = (
        await db.execute(
            select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
        )
    ).scalar_one()
    total_saved_events = (await db.execute(text("SELECT COUNT(*) FROM saved_events"))).scalar_one()

    total_events, total_swipes = await asyncio.gather(
        _count_events(),
        asyncio.to_thread(_count_swipes_sync),
    )

    return StatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_events=total_events,
        total_saved_events=total_saved_events,
        total_swipes=total_swipes,
    )
