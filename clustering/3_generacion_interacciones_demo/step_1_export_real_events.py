from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from demo_config import (
    DEFAULT_DATASET,
    DEFAULT_EVENTS_TABLE,
    DEFAULT_PROJECT_ID,
    REAL_EVENTS_PATH,
    ensure_output_dir,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export real catalog events from BigQuery to a local CSV for synthetic swipe generation."
    )
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--events-table", default=DEFAULT_EVENTS_TABLE)
    parser.add_argument("--output-csv", type=Path, default=REAL_EVENTS_PATH)
    parser.add_argument("--limit", type=int, default=0, help="Optional row limit. 0 means no limit.")
    return parser.parse_args()


def build_sql(project_id: str, dataset: str, table: str, limit: int) -> str:
    limit_clause = f"\nlimit {limit}" if limit > 0 else ""
    return f"""
select
  cast(id as string) as id,
  nombre,
  cast(fecha as string) as fecha,
  segmento,
  genero,
  subgenero,
  recinto_id,
  ciudad,
  categoria,
  subcategoria,
  banda_precio
from `{project_id}.{dataset}.{table}`
where id is not null
  and fecha is not null
  and ciudad is not null
  and banda_precio is not null
order by fecha, ciudad, id{limit_clause}
""".strip()


def run_bq_query(project_id: str, sql: str) -> str:
    command = [
        "bq",
        "query",
        f"--project_id={project_id}",
        "--use_legacy_sql=false",
        "--format=csv",
        "--max_rows=100000",
        sql,
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def main() -> None:
    args = parse_args()
    ensure_output_dir()

    sql = build_sql(args.project_id, args.dataset, args.events_table, args.limit)
    csv_content = run_bq_query(args.project_id, sql)

    if not csv_content.strip():
        raise RuntimeError("BigQuery returned no events. Check project, dataset and table names.")

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_csv.write_text(csv_content, encoding="utf-8")

    row_count = max(0, len(csv_content.splitlines()) - 1)
    print(f"Exported {row_count} real events to {args.output_csv}")


if __name__ == "__main__":
    main()
