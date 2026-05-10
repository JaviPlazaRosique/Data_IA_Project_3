from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,1023}$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{4,61}[a-z0-9]$")
_ENV_PATH = Path(__file__).resolve().parent / ".env"


def _first_env(*names: str, default: str = "") -> str:
    for name in names:
        value = os.getenv(name)
        if value:
            return value.strip()
    return default


class AgentSettings(BaseSettings):
    project_id: str = Field(default_factory=lambda: _first_env("APP_PROJECT_ID", "PROJECT_ID", "GOOGLE_CLOUD_PROJECT"))
    region: str = Field(default_factory=lambda: _first_env("APP_REGION", "REGION", "GOOGLE_CLOUD_LOCATION", default="europe-west1"))

    bigquery_dataset: str = Field(default="recomendacion_planes", alias="BIGQUERY_DATASET")
    bigquery_rag_table: str = Field(default="eventos", alias="BIGQUERY_RAG_TABLE")

    embedding_model: str = Field(default="gemini-embedding-001", alias="EMBEDDING_MODEL")
    embedding_dimension: int = Field(default=3072, alias="EMBEDDING_DIMENSION")
    agent_model: str = Field(default="gemini-2.5-flash", alias="AGENT_MODEL")

    model_config = SettingsConfigDict(env_file=str(_ENV_PATH), env_file_encoding="utf-8", extra="ignore")

    @field_validator("project_id")
    @classmethod
    def validate_project_id(cls, value: str) -> str:
        if value and not _PROJECT_RE.match(value):
            raise ValueError("PROJECT_ID no parece un ID válido de Google Cloud")
        return value

    @field_validator("bigquery_dataset", "bigquery_rag_table")
    @classmethod
    def validate_bigquery_identifier(cls, value: str) -> str:
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Identificador BigQuery inválido: {value!r}")
        return value

    @property
    def rag_table_fqn(self) -> str:
        return quote_table_fqn(self.project_id, self.bigquery_dataset, self.bigquery_rag_table)


def quote_table_fqn(project_id: str, dataset: str, table: str) -> str:
    if not project_id:
        raise ValueError("PROJECT_ID es obligatorio para construir tablas BigQuery")
    if not _PROJECT_RE.match(project_id):
        raise ValueError("PROJECT_ID inválido")
    for value in (dataset, table):
        if not _IDENTIFIER_RE.match(value):
            raise ValueError(f"Identificador BigQuery inválido: {value!r}")
    return f"`{project_id}.{dataset}.{table}`"


@lru_cache(maxsize=1)
def get_settings() -> AgentSettings:
    return AgentSettings()
