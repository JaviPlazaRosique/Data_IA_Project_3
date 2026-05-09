import asyncio
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.auth.dependencies import get_admin_user
from app.config import settings
from app.db.bigquery import bq_table, get_bq_client
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


class SwipeTotals(BaseModel):
    left: int
    right: int


class DailySwipe(BaseModel):
    date: str
    left: int
    right: int


class AnalyticsResponse(BaseModel):
    swipe_totals: SwipeTotals
    daily_swipes: list[DailySwipe]


def _query_analytics_sync() -> AnalyticsResponse:
    try:
        table = bq_table(settings.BIGQUERY_MARTS_DATASET, "fct_swipes")
        client = get_bq_client()

        totals_query = f"""
            SELECT
                COUNTIF(direction = 'left') AS left_count,
                COUNTIF(direction = 'right') AS right_count
            FROM {table}
        """
        totals_rows = list(client.query(totals_query).result())
        if totals_rows:
            row = totals_rows[0]
            totals = SwipeTotals(left=row["left_count"] or 0, right=row["right_count"] or 0)
        else:
            totals = SwipeTotals(left=0, right=0)

        daily_query = f"""
            SELECT
                CAST(DATE(timestamp) AS STRING) AS date,
                COUNTIF(direction = 'left') AS left_count,
                COUNTIF(direction = 'right') AS right_count
            FROM {table}
            WHERE DATE(timestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 30 DAY)
            GROUP BY date
            ORDER BY date ASC
        """
        daily = [
            DailySwipe(date=r["date"], left=r["left_count"] or 0, right=r["right_count"] or 0)
            for r in client.query(daily_query).result()
        ]

        return AnalyticsResponse(swipe_totals=totals, daily_swipes=daily)

    except Exception:
        logger.exception("Failed to query analytics from BigQuery")
        return AnalyticsResponse(swipe_totals=SwipeTotals(left=0, right=0), daily_swipes=[])


@router.get("", response_model=AnalyticsResponse)
async def get_analytics(_: User = Depends(get_admin_user)) -> AnalyticsResponse:
    return await asyncio.to_thread(_query_analytics_sync)
