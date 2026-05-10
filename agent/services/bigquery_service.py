from __future__ import annotations

import argparse
import datetime as _dt
import json
import logging
import math
import time
from dataclasses import dataclass
from datetime import date
from typing import Any

from agent.config import AgentSettings, get_settings, quote_table_fqn
from agent.services.embedding_service import EmbeddingService

try:
    from google.cloud import bigquery
except Exception:
    bigquery = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)
MIN_VECTOR_INDEX_ROWS = 5000
DEFAULT_VERIFY_QUESTION = "concierto de rock un viernes por la noche"


class BigQueryServiceError(RuntimeError):
    pass


def validate_embedding(vector: list[float]) -> list[float]:
    if not vector:
        raise ValueError("El embedding no puede estar vacío")
    if any(math.isnan(v) or math.isinf(v) for v in vector):
        raise ValueError("El embedding contiene NaN o infinito")
    return vector


def build_vector_search_sql(rag_table_fqn: str) -> str:
    return f"""
SELECT
  base.id              AS id,
  base.nombre          AS title,
  base.categoria       AS category,
  base.ciudad          AS ciudad,
  base.franja_horaria  AS franja_horaria,
  base.contexto_rag    AS content,
  base.url             AS source_url,
  base.fecha           AS fecha_evento,
  CURRENT_TIMESTAMP()  AS updated_at,
  distance
FROM VECTOR_SEARCH(
  (
    SELECT id, nombre, categoria, ciudad, franja_horaria, contexto_rag, url, fecha, embedding
    FROM {rag_table_fqn}
    WHERE ARRAY_LENGTH(embedding) = @embedding_dim
      AND (@category IS NULL OR categoria = @category)
      AND (@ciudad IS NULL OR ciudad = @ciudad)
      AND (@franja_horaria IS NULL OR franja_horaria = @franja_horaria)
      AND (@date_from IS NULL OR fecha >= CAST(@date_from AS DATE))
      AND (@date_to   IS NULL OR fecha <= CAST(@date_to   AS DATE))
  ),
  'embedding',
  (SELECT @query_embedding AS embedding, @query_text AS query_text),
  top_k => @top_k,
  distance_type => 'COSINE',
  options => '{{"use_brute_force": true}}'
)
ORDER BY distance ASC
""".strip()


def _serialize_row(row: Any) -> dict[str, Any]:
    raw = dict(row.items()) if hasattr(row, "items") else dict(row)
    return {
        k: v.isoformat() if isinstance(v, (_dt.date, _dt.datetime)) else v
        for k, v in raw.items()
    }


@dataclass(slots=True)
class BigQueryRagService:
    settings: AgentSettings | None = None
    client: Any | None = None

    def __post_init__(self) -> None:
        if self.settings is None:
            self.settings = get_settings()
        if self.client is None:
            if bigquery is None:
                raise BigQueryServiceError("google-cloud-bigquery no está instalado")
            self.client = bigquery.Client(project=self.settings.project_id or None)

    @property
    def rag_table_fqn(self) -> str:
        return quote_table_fqn(self.settings.project_id, self.settings.bigquery_dataset, self.settings.bigquery_rag_table)

    def ensure_dataset_and_table(self) -> None:
        if bigquery is None:
            raise BigQueryServiceError("google-cloud-bigquery no está instalado")
        dataset_ref = f"{self.settings.project_id}.{self.settings.bigquery_dataset}"
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = self.settings.region
        self.client.create_dataset(dataset, exists_ok=True)

        logger.info("ensure_ok dataset=%s (la tabla eventos la gestiona el pipeline Dataflow)", dataset_ref)

    def count_eventos(self) -> int:
        sql = f"SELECT COUNT(1) AS row_count FROM {self.rag_table_fqn}"
        rows = list(self.client.query(sql).result())
        if not rows:
            return 0
        row = rows[0]
        if hasattr(row, "get"):
            return int(row.get("row_count", 0))
        if hasattr(row, "row_count"):
            return int(row.row_count)
        return int(row[0])

    def create_vector_index(self) -> str:
        row_count = self.count_eventos()
        if row_count < MIN_VECTOR_INDEX_ROWS:
            return (
                f"Índice no creado: la tabla tiene {row_count} filas y BigQuery requiere al menos "
                f"{MIN_VECTOR_INDEX_ROWS} para CREATE VECTOR INDEX IVF. "
                "VECTOR_SEARCH sigue funcionando con use_brute_force=true."
            )
        sql = f"""
CREATE VECTOR INDEX IF NOT EXISTS eventos_embedding_idx
ON {self.rag_table_fqn}(embedding)
STORING(id, nombre, categoria, url, fecha)
OPTIONS(index_type = 'IVF', distance_type = 'COSINE')
""".strip()
        self.client.query(sql).result()
        return f"Índice creado sobre {self.rag_table_fqn}"

    def rag_search(
        self,
        question: str,
        embedding_service: EmbeddingService,
        *,
        top_k: int = 5,
        category: str | None = None,
        ciudad: str | None = None,
        franja_horaria: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        question = question.strip()
        if not question:
            raise ValueError("La pregunta RAG no puede estar vacía")
        top_k = max(1, min(int(top_k), 20))
        today_iso = date.today().isoformat()
        if not date_from or date_from < today_iso:
            date_from = today_iso

        embed_t0 = time.perf_counter()
        query_embedding = validate_embedding(embedding_service.embed_query(question))
        embed_ms = round((time.perf_counter() - embed_t0) * 1000, 1)

        if bigquery is None:
            raise BigQueryServiceError("google-cloud-bigquery no está instalado")
        params = [
            bigquery.ArrayQueryParameter("query_embedding", "FLOAT64", query_embedding),
            bigquery.ScalarQueryParameter("embedding_dim", "INT64", len(query_embedding)),
            bigquery.ScalarQueryParameter("top_k", "INT64", top_k),
            bigquery.ScalarQueryParameter("category", "STRING", category),
            bigquery.ScalarQueryParameter("ciudad", "STRING", ciudad),
            bigquery.ScalarQueryParameter("franja_horaria", "STRING", franja_horaria),
            bigquery.ScalarQueryParameter("query_text", "STRING", question),
            bigquery.ScalarQueryParameter("date_from", "STRING", date_from),
            bigquery.ScalarQueryParameter("date_to", "STRING", date_to),
        ]
        job_config = bigquery.QueryJobConfig(query_parameters=params)

        bq_t0 = time.perf_counter()
        rows = self.client.query(build_vector_search_sql(self.rag_table_fqn), job_config=job_config).result()
        results = [_serialize_row(row) for row in rows]
        bq_ms = round((time.perf_counter() - bq_t0) * 1000, 1)

        logger.info(
            "rag_search_done",
            extra={
                "question_len": len(question),
                "top_k": top_k,
                "category": category,
                "ciudad": ciudad,
                "franja_horaria": franja_horaria,
                "date_from": date_from,
                "date_to": date_to,
                "embed_ms": embed_ms,
                "bq_ms": bq_ms,
                "count": len(results),
                "distance_top1": results[0].get("distance") if results else None,
            },
        )
        return results

    def verify_rag(self, question: str = DEFAULT_VERIFY_QUESTION, *, top_k: int = 3) -> list[dict[str, Any]]:
        rows = self.rag_search(question, EmbeddingService(settings=self.settings), top_k=top_k)
        if not rows:
            raise BigQueryServiceError(
                "RAG no devolvió resultados. Asegúrate de haber ejecutado el pipeline Dataflow "
                "para que la tabla eventos tenga embeddings."
            )
        return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="Utilidades BigQuery RAG para eventos")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("ensure", help="Crea el dataset si falta (la tabla eventos la gestiona el pipeline)")
    sub.add_parser("index",  help="Crea índice vectorial IVF si la tabla tiene suficientes filas")

    verify = sub.add_parser("verify", help="Verifica que RAG devuelve resultados con VECTOR_SEARCH")
    verify.add_argument("question", nargs="?", default=DEFAULT_VERIFY_QUESTION)
    verify.add_argument("--top-k", type=int, default=3)

    search = sub.add_parser("search", help="Ejecuta VECTOR_SEARCH con una pregunta")
    search.add_argument("question")
    search.add_argument("--top-k", type=int, default=5)

    args = parser.parse_args()
    service = BigQueryRagService()

    if args.command == "ensure":
        service.ensure_dataset_and_table()
        print("Dataset y tabla listos")
    elif args.command == "index":
        print(service.create_vector_index())
    elif args.command == "verify":
        rows = service.verify_rag(args.question, top_k=args.top_k)
        print(json.dumps({"status": "ok", "rag_results": len(rows), "results": rows}, indent=2, ensure_ascii=False, default=str))
    elif args.command == "search":
        rows = service.rag_search(args.question, EmbeddingService(), top_k=args.top_k)
        print(json.dumps(rows, indent=2, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
