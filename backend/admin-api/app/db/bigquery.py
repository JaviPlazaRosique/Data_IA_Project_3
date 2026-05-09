import re
from functools import lru_cache

from google.cloud import bigquery

from app.config import settings

_SAFE_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def _safe(value: str, label: str) -> str:
    if not _SAFE_ID.fullmatch(value):
        raise RuntimeError(f"Invalid BigQuery {label}: {value!r}")
    return value


@lru_cache(maxsize=1)
def get_bq_client() -> bigquery.Client:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT or None
    return bigquery.Client(project=project_id)


def bq_table(dataset: str, table: str) -> str:
    project_id = settings.BIGQUERY_PROJECT_ID or settings.GOOGLE_CLOUD_PROJECT
    if not project_id:
        raise RuntimeError("BIGQUERY_PROJECT_ID or GOOGLE_CLOUD_PROJECT must be set")
    return f"`{_safe(project_id, 'project')}.{_safe(dataset, 'dataset')}.{_safe(table, 'table')}`"
