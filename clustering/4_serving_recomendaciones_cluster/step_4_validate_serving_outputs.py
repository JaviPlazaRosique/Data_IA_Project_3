from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from serving_config import (
    DEFAULT_MARTS_DATASET,
    DEFAULT_PROJECT_ID,
    VALIDATION_SUMMARY_PATH,
    ensure_output_dir,
    table,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate clustering serving tables in BigQuery.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--marts-dataset", default=DEFAULT_MARTS_DATASET)
    parser.add_argument("--summary-json", type=Path, default=VALIDATION_SUMMARY_PATH)
    return parser.parse_args()


def run_bq_json(project_id: str, sql: str) -> list[dict[str, str]]:
    completed = subprocess.run(
        [
            "bq",
            "query",
            f"--project_id={project_id}",
            "--use_legacy_sql=false",
            "--format=prettyjson",
            sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(completed.stdout)


def counts_sql(project_id: str, dataset: str) -> str:
    assignments = table(project_id, dataset, "user_cluster_assignments")
    profiles = table(project_id, dataset, "cluster_profiles")
    neighbors = table(project_id, dataset, "cluster_neighbors")
    affinity = table(project_id, dataset, "cluster_event_affinity")
    candidates = table(project_id, dataset, "user_recommendation_candidates")
    return f"""
select
  (select count(*) from {assignments}) as assignment_rows,
  (select count(distinct user_id) from {assignments}) as assigned_users,
  (select count(*) from {profiles}) as cluster_profile_rows,
  (select count(*) from {neighbors}) as cluster_neighbor_rows,
  (select count(*) from {affinity}) as cluster_event_affinity_rows,
  (select count(*) from {candidates}) as recommendation_rows,
  (select count(distinct user_id) from {candidates}) as users_with_recommendations,
  (select avg(recommendation_score) from {candidates} where recommendation_rank <= 5) as avg_top5_score,
  (select max(recommendation_rank) from {candidates}) as max_recommendation_rank
""".strip()


def sample_sql(project_id: str, dataset: str) -> str:
    candidates = table(project_id, dataset, "user_recommendation_candidates")
    return f"""
select
  user_id,
  user_cluster_id,
  recommendation_rank,
  event_id,
  event_name,
  segmento,
  genero,
  ciudad,
  cluster_source,
  recommendation_score
from {candidates}
where recommendation_rank <= 3
order by user_id, recommendation_rank
limit 20
""".strip()


def main() -> None:
    args = parse_args()
    ensure_output_dir()

    counts = run_bq_json(args.project_id, counts_sql(args.project_id, args.marts_dataset))
    sample = run_bq_json(args.project_id, sample_sql(args.project_id, args.marts_dataset))
    summary = {
        "project_id": args.project_id,
        "marts_dataset": args.marts_dataset,
        "counts": counts[0] if counts else {},
        "sample_top_recommendations": sample,
    }
    args.summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("Serving validation summary")
    for key, value in summary["counts"].items():
        print(f"- {key}: {value}")
    print(f"Validation JSON: {args.summary_json}")


if __name__ == "__main__":
    main()
