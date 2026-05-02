from __future__ import annotations

import asyncio
import re
from functools import lru_cache

from google.cloud import bigquery

from app.config import settings
from app.schemas.recommendation import ClusterRecommendationRead

SAFE_BQ_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


@lru_cache(maxsize=1)
def _get_bigquery_client() -> bigquery.Client:
    project_id = settings.GOOGLE_CLOUD_PROJECT or None
    return bigquery.Client(project=project_id)


def _safe_identifier(value: str, label: str) -> str:
    if not SAFE_BQ_IDENTIFIER.fullmatch(value):
        raise RuntimeError(f"Invalid BigQuery {label}: {value!r}")
    return value


def _recommendations_table() -> str:
    project_id = settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("GOOGLE_CLOUD_PROJECT must be set to read recommendations from BigQuery")
    project_id = _safe_identifier(project_id, "project id")
    dataset = _safe_identifier(settings.BIGQUERY_MARTS_DATASET, "dataset")
    table = _safe_identifier(settings.BIGQUERY_RECOMMENDATIONS_TABLE, "table")
    return (
        f"`{project_id}."
        f"{dataset}."
        f"{table}`"
    )


def _query_recommendations_sync(user_id: str, limit: int) -> list[ClusterRecommendationRead]:
    query = f"""
select
  event_id,
  event_name,
  cast(fecha_evento as string) as fecha_evento,
  ciudad,
  recinto_nombre,
  segmento,
  genero,
  subgenero,
  recommendation_rank,
  recommendation_score,
  cluster_source
from {_recommendations_table()}
where user_id = @user_id
order by recommendation_rank asc
limit @limit
""".strip()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("user_id", "STRING", user_id),
            bigquery.ScalarQueryParameter("limit", "INT64", limit),
        ],
    )
    rows = _get_bigquery_client().query(query, job_config=job_config).result()
    return [ClusterRecommendationRead(**dict(row.items())) for row in rows]


async def list_user_recommendations(user_id: str, limit: int) -> list[ClusterRecommendationRead]:
    return await asyncio.to_thread(_query_recommendations_sync, user_id, limit)
