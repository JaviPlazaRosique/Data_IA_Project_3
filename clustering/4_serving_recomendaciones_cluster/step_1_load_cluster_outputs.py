from __future__ import annotations

import argparse
import csv
import re
import subprocess
import tempfile
from pathlib import Path

from serving_config import (
    DEFAULT_MARTS_DATASET,
    DEFAULT_MODEL_RUN_ID,
    DEFAULT_PROJECT_ID,
    DEFAULT_TRAINING_OUTPUT_DIR,
    safe_sql_literal,
    table,
)


SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")

ASSIGNMENTS_SCHEMA = (
    "user_id:STRING,home_city:STRING,reference_city:STRING,reference_city_source:STRING,"
    "synthetic_persona:STRING,cluster_id:INT64,"
    "distance_to_centroid:FLOAT64,distance_to_next_centroid:FLOAT64"
)
PROFILES_SCHEMA = (
    "cluster_id:INT64,cluster_size:INT64,share_of_users:FLOAT64,"
    "dominant_synthetic_persona:STRING,dominant_synthetic_persona_share:FLOAT64,"
    "dominant_home_city:STRING,dominant_home_city_share:FLOAT64,"
    "top_segment_1:STRING,top_segment_2:STRING,top_genre_1:STRING,top_genre_2:STRING"
)
NEIGHBORS_SCHEMA = (
    "cluster_id:INT64,neighbor_rank:INT64,neighbor_cluster_id:INT64,"
    "euclidean_distance:FLOAT64,cosine_similarity:FLOAT64"
)
ASSIGNMENTS_COLUMNS = [
    "user_id",
    "home_city",
    "reference_city",
    "reference_city_source",
    "synthetic_persona",
    "cluster_id",
    "distance_to_centroid",
    "distance_to_next_centroid",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Load clustering model outputs into BigQuery serving tables.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--marts-dataset", default=DEFAULT_MARTS_DATASET)
    parser.add_argument("--training-output-dir", type=Path, default=DEFAULT_TRAINING_OUTPUT_DIR)
    parser.add_argument("--model-run-id", default=DEFAULT_MODEL_RUN_ID)
    return parser.parse_args()


def validate_safe_id(value: str, label: str) -> None:
    if not SAFE_ID_PATTERN.fullmatch(value):
        raise ValueError(f"Unsafe {label}: {value!r}. Use only letters, numbers and underscores.")


def run_command(command: list[str]) -> None:
    subprocess.run(command, check=True)


def run_query(project_id: str, sql: str) -> None:
    run_command(
        [
            "bq",
            "query",
            f"--project_id={project_id}",
            "--use_legacy_sql=false",
            "--quiet",
            sql,
        ]
    )


def load_csv(project_id: str, destination: str, csv_path: Path, schema: str) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV: {csv_path}")
    run_command(
        [
            "bq",
            "load",
            f"--project_id={project_id}",
            "--replace",
            "--source_format=CSV",
            "--skip_leading_rows=1",
            destination,
            str(csv_path),
            schema,
        ]
    )


def normalize_assignments_csv(csv_path: Path) -> Path:
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        if reader.fieldnames == ASSIGNMENTS_COLUMNS:
            return csv_path

    temp = tempfile.NamedTemporaryFile("w", newline="", encoding="utf-8", suffix=".csv", delete=False)
    with temp:
        writer = csv.DictWriter(temp, fieldnames=ASSIGNMENTS_COLUMNS)
        writer.writeheader()
        for row in rows:
            reference_city = row.get("reference_city") or row.get("home_city") or ""
            writer.writerow(
                {
                    "user_id": row.get("user_id", ""),
                    "home_city": row.get("home_city") or reference_city,
                    "reference_city": reference_city,
                    "reference_city_source": row.get("reference_city_source", ""),
                    "synthetic_persona": row.get("synthetic_persona", ""),
                    "cluster_id": row.get("cluster_id", ""),
                    "distance_to_centroid": row.get("distance_to_centroid", ""),
                    "distance_to_next_centroid": row.get("distance_to_next_centroid", ""),
                }
            )
    return Path(temp.name)


def create_assignments_sql(project_id: str, dataset: str, tmp_table: str, model_run_id: str) -> str:
    escaped_run_id = safe_sql_literal(model_run_id)
    return f"""
create or replace table {table(project_id, dataset, "user_cluster_assignments")}
cluster by cluster_id, user_id as
select
  '{escaped_run_id}' as model_run_id,
  current_timestamp() as model_run_at,
  user_id,
  nullif(home_city, '') as home_city,
  nullif(reference_city, '') as reference_city,
  nullif(reference_city_source, '') as reference_city_source,
  nullif(synthetic_persona, '') as synthetic_persona,
  cluster_id,
  distance_to_centroid,
  distance_to_next_centroid
from {table(project_id, dataset, tmp_table)}
""".strip()


def create_profiles_sql(project_id: str, dataset: str, tmp_table: str, model_run_id: str) -> str:
    escaped_run_id = safe_sql_literal(model_run_id)
    return f"""
create or replace table {table(project_id, dataset, "cluster_profiles")}
cluster by cluster_id as
select
  '{escaped_run_id}' as model_run_id,
  current_timestamp() as model_run_at,
  cluster_id,
  cluster_size,
  share_of_users,
  dominant_synthetic_persona,
  dominant_synthetic_persona_share,
  dominant_home_city,
  dominant_home_city_share,
  top_segment_1,
  top_segment_2,
  top_genre_1,
  top_genre_2
from {table(project_id, dataset, tmp_table)}
""".strip()


def create_neighbors_sql(project_id: str, dataset: str, tmp_table: str, model_run_id: str) -> str:
    escaped_run_id = safe_sql_literal(model_run_id)
    return f"""
create or replace table {table(project_id, dataset, "cluster_neighbors")}
cluster by cluster_id, neighbor_rank as
select
  '{escaped_run_id}' as model_run_id,
  current_timestamp() as model_run_at,
  cluster_id,
  neighbor_rank,
  neighbor_cluster_id,
  euclidean_distance,
  cosine_similarity
from {table(project_id, dataset, tmp_table)}
""".strip()


def main() -> None:
    args = parse_args()
    validate_safe_id(args.model_run_id, "model_run_id")

    run_suffix = args.model_run_id.lower()
    tmp_assignments = f"_tmp_user_cluster_assignments_{run_suffix}"
    tmp_profiles = f"_tmp_cluster_profiles_{run_suffix}"
    tmp_neighbors = f"_tmp_cluster_neighbors_{run_suffix}"

    load_csv(
        args.project_id,
        f"{args.project_id}:{args.marts_dataset}.{tmp_assignments}",
        normalize_assignments_csv(args.training_output_dir / "user_cluster_assignments.csv"),
        ASSIGNMENTS_SCHEMA,
    )
    load_csv(
        args.project_id,
        f"{args.project_id}:{args.marts_dataset}.{tmp_profiles}",
        args.training_output_dir / "cluster_profiles.csv",
        PROFILES_SCHEMA,
    )
    load_csv(
        args.project_id,
        f"{args.project_id}:{args.marts_dataset}.{tmp_neighbors}",
        args.training_output_dir / "cluster_neighbors.csv",
        NEIGHBORS_SCHEMA,
    )

    run_query(args.project_id, create_assignments_sql(args.project_id, args.marts_dataset, tmp_assignments, args.model_run_id))
    run_query(args.project_id, create_profiles_sql(args.project_id, args.marts_dataset, tmp_profiles, args.model_run_id))
    run_query(args.project_id, create_neighbors_sql(args.project_id, args.marts_dataset, tmp_neighbors, args.model_run_id))

    print("Loaded clustering outputs into BigQuery serving tables:")
    print(f"- {args.project_id}.{args.marts_dataset}.user_cluster_assignments")
    print(f"- {args.project_id}.{args.marts_dataset}.cluster_profiles")
    print(f"- {args.project_id}.{args.marts_dataset}.cluster_neighbors")


if __name__ == "__main__":
    main()
