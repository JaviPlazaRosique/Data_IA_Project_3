from __future__ import annotations

import asyncio
import logging
import re

from google.cloud import bigquery

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

SAFE_BQ_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


def _safe_identifier(value: str, label: str) -> str:
    if not SAFE_BQ_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Invalid BigQuery {label}: {value!r}")
    return value


def _preferences_table() -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set to sync user preferences")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_ANALYTICS_DATASET, "dataset")
    table = _safe_identifier(settings.BIGQUERY_USER_PREFERENCES_TABLE, "table")
    return f"`{project_id}.{dataset}.{table}`"


def _sync_user_preferences_sync(user: User) -> None:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT or None
    client = bigquery.Client(project=project_id)
    query = f"""
merge {_preferences_table()} target
using (
  select
    @user_id as user_id,
    @preferred_location as preferred_location,
    @preferred_location_lat as preferred_location_lat,
    @preferred_location_lng as preferred_location_lng,
    @preferred_budget as preferred_budget,
    current_timestamp() as synced_at
) source
on target.user_id = source.user_id
when matched then update set
  preferred_location = source.preferred_location,
  preferred_location_lat = source.preferred_location_lat,
  preferred_location_lng = source.preferred_location_lng,
  preferred_budget = source.preferred_budget,
  synced_at = source.synced_at
when not matched then insert (
  user_id,
  preferred_location,
  preferred_location_lat,
  preferred_location_lng,
  preferred_budget,
  synced_at
) values (
  source.user_id,
  source.preferred_location,
  source.preferred_location_lat,
  source.preferred_location_lng,
  source.preferred_budget,
  source.synced_at
)
""".strip()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", str(user.id)),
            bigquery.ScalarQueryParameter("preferred_location", "STRING", user.preferred_location),
            bigquery.ScalarQueryParameter("preferred_location_lat", "FLOAT64", user.preferred_location_lat),
            bigquery.ScalarQueryParameter("preferred_location_lng", "FLOAT64", user.preferred_location_lng),
            bigquery.ScalarQueryParameter("preferred_budget", "STRING", user.preferred_budget),
        ],
    )
    client.query(query, job_config=job_config).result()


async def sync_user_preferences(user: User) -> None:
    if not settings.BIGQUERY_USER_PREFERENCES_SYNC_ENABLED:
        return
    if not (settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT):
        return

    try:
        await asyncio.to_thread(_sync_user_preferences_sync, user)
    except Exception:
        logger.exception("Failed to sync user preferences to BigQuery user_id=%s", user.id)
