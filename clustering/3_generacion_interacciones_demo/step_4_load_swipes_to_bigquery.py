from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

from demo_config import (
    DEFAULT_DATASET,
    DEFAULT_PROJECT_ID,
    DEFAULT_SWIPES_TABLE,
    SYNTHETIC_SWIPES_JSONL_PATH,
)


RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Append generated synthetic swipe rows to BigQuery swipes_raw.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--table", default=DEFAULT_SWIPES_TABLE)
    parser.add_argument("--raw-jsonl", type=Path, default=SYNTHETIC_SWIPES_JSONL_PATH)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Load even if rows with the same synthetic_run_id already exist.",
    )
    return parser.parse_args()


def first_payload(path: Path) -> dict[str, str]:
    with path.open(encoding="utf-8") as file:
        for line in file:
            if line.strip():
                row = json.loads(line)
                return json.loads(row["data"])
    raise RuntimeError(f"{path} is empty")


def count_jsonl_rows(path: Path) -> int:
    with path.open(encoding="utf-8") as file:
        return sum(1 for line in file if line.strip())


def run_bq_query(project_id: str, sql: str) -> str:
    command = [
        "bq",
        "query",
        f"--project_id={project_id}",
        "--use_legacy_sql=false",
        "--format=csv",
        sql,
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    return completed.stdout


def existing_rows(project_id: str, dataset: str, table: str, run_id: str) -> int:
    if not RUN_ID_PATTERN.fullmatch(run_id):
        raise ValueError(f"Unsafe synthetic_run_id: {run_id!r}")
    sql = f"""
select count(*) as existing_rows
from `{project_id}.{dataset}.{table}`
where json_value(data, '$.synthetic_run_id') = '{run_id}'
""".strip()
    result = run_bq_query(project_id, sql)
    lines = [line.strip() for line in result.splitlines() if line.strip()]
    return int(lines[1]) if len(lines) > 1 else 0


def load_jsonl(project_id: str, dataset: str, table: str, path: Path) -> None:
    destination = f"{project_id}:{dataset}.{table}"
    command = [
        "bq",
        "load",
        f"--project_id={project_id}",
        "--source_format=NEWLINE_DELIMITED_JSON",
        "--noreplace",
        "--max_bad_records=0",
        destination,
        str(path),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    if not args.raw_jsonl.exists():
        raise FileNotFoundError(f"Missing generated JSONL: {args.raw_jsonl}")

    payload = first_payload(args.raw_jsonl)
    run_id = payload.get("synthetic_run_id")
    if not run_id:
        raise RuntimeError("Generated payload does not contain synthetic_run_id")

    row_count = count_jsonl_rows(args.raw_jsonl)
    already_loaded = existing_rows(args.project_id, args.dataset, args.table, run_id)
    if already_loaded > 0 and not args.force:
        raise RuntimeError(
            f"Found {already_loaded} existing rows for synthetic_run_id={run_id}. "
            "Use --force only if you intentionally want to append duplicates to raw."
        )

    load_jsonl(args.project_id, args.dataset, args.table, args.raw_jsonl)
    print(
        f"Loaded {row_count} rows into {args.project_id}:{args.dataset}.{args.table} "
        f"with synthetic_run_id={run_id}"
    )


if __name__ == "__main__":
    main()
