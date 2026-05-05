from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from demo_config import (
    DEFAULT_DATASET,
    DEFAULT_PROJECT_ID,
    DEFAULT_RUN_ID,
    DEFAULT_SWIPES_TABLE,
    VALIDATION_SUMMARY_PATH,
)


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate synthetic demo swipes loaded in BigQuery.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--table", default=DEFAULT_SWIPES_TABLE)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--summary-json", type=Path, default=VALIDATION_SUMMARY_PATH)
    return parser.parse_args()


def run_bq_json(project_id: str, sql: str) -> list[dict[str, str]]:
    command = [
        "bq",
        "query",
        f"--project_id={project_id}",
        "--use_legacy_sql=false",
        "--format=prettyjson",
        sql,
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(completed.stdout)


def validate_run_id(run_id: str) -> None:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"Unsafe synthetic_run_id: {run_id!r}")


def build_summary_sql(project_id: str, dataset: str, table: str, run_id: str) -> str:
    return f"""
select
  count(*) as rows_loaded,
  count(distinct json_value(data, '$.user_id')) as users,
  count(distinct json_value(data, '$.event_id')) as events,
  countif(json_value(data, '$.schema_version') = '2.0') as rows_v2,
  countif(json_value(data, '$.event_snapshot.event_id') is not null) as rows_with_snapshot,
  countif(safe_cast(json_value(data, '$.dwell_ms') as int64) is not null) as rows_with_dwell_ms,
  avg(safe_cast(json_value(data, '$.dwell_ms') as int64)) as avg_dwell_ms,
  safe_divide(countif(json_value(data, '$.direction') = 'right'), count(*)) as right_swipe_rate,
  min(safe_cast(json_value(data, '$.swiped_at') as timestamp)) as min_swiped_at,
  max(safe_cast(json_value(data, '$.swiped_at') as timestamp)) as max_swiped_at,
  count(distinct json_value(data, '$.event_snapshot.segmento')) as distinct_segments,
  count(distinct json_value(data, '$.event_snapshot.genero')) as distinct_genres
from `{project_id}.{dataset}.{table}`
where json_value(data, '$.synthetic_run_id') = '{run_id}'
""".strip()


def build_persona_sql(project_id: str, dataset: str, table: str, run_id: str) -> str:
    return f"""
select
  json_value(data, '$.synthetic_persona') as persona,
  count(*) as rows_loaded,
  safe_divide(countif(json_value(data, '$.direction') = 'right'), count(*)) as right_swipe_rate
from `{project_id}.{dataset}.{table}`
where json_value(data, '$.synthetic_run_id') = '{run_id}'
group by persona
order by persona
""".strip()


def main() -> None:
    args = parse_args()
    validate_run_id(args.run_id)

    summary_rows = run_bq_json(
        args.project_id,
        build_summary_sql(args.project_id, args.dataset, args.table, args.run_id),
    )
    persona_rows = run_bq_json(
        args.project_id,
        build_persona_sql(args.project_id, args.dataset, args.table, args.run_id),
    )

    summary = {
        "run_id": args.run_id,
        "table": f"{args.project_id}.{args.dataset}.{args.table}",
        "summary": summary_rows[0] if summary_rows else {},
        "personas": persona_rows,
    }
    args.summary_json.parent.mkdir(parents=True, exist_ok=True)
    args.summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rows_loaded = summary["summary"].get("rows_loaded", "0")
    users = summary["summary"].get("users", "0")
    right_rate = summary["summary"].get("right_swipe_rate", "0")
    print(f"Validated run_id={args.run_id}: {rows_loaded} rows, {users} users, right_rate={right_rate}")
    print(f"Validation summary: {args.summary_json}")


if __name__ == "__main__":
    main()
