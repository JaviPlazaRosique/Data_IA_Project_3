from __future__ import annotations

import csv
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from google.cloud import bigquery


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[2]
SERVING_DIR = REPO_ROOT / "clustering" / "4_serving_recomendaciones_cluster"
TRAINING_SCRIPT = (
    REPO_ROOT
    / "clustering"
    / "2_integracion_datos_gcp"
    / "step_4_entrenar_desde_feature_export.py"
)

LOCAL_WORKDIR = Path(os.environ.get("LOCAL_WORKDIR", "/tmp/clustering_job"))
FEATURE_EXPORT_CSV = LOCAL_WORKDIR / "dim_user_cluster_features_current.csv"
TRAINING_OUTPUT_DIR = LOCAL_WORKDIR / "training_outputs"

SAFE_BQ_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")
SAFE_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def log(event: str, **payload: object) -> None:
    print(json.dumps({"event": event, **payload}, ensure_ascii=True), flush=True)


def env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    return int(value) if value not in {None, ""} else default


def env_str(name: str, default: str) -> str:
    value = os.environ.get(name)
    return value if value not in {None, ""} else default


def safe_identifier(value: str, label: str, *, allow_hyphen: bool = True) -> str:
    pattern = SAFE_BQ_ID_PATTERN if allow_hyphen else SAFE_RUN_ID_PATTERN
    if not pattern.fullmatch(value):
        allowed = "letters, numbers, underscores and hyphens" if allow_hyphen else "letters, numbers and underscores"
        raise RuntimeError(f"Unsafe {label}: {value!r}. Use {allowed} only.")
    return value


def model_run_id() -> str:
    explicit = os.environ.get("MODEL_RUN_ID")
    if explicit:
        return safe_identifier(explicit, "MODEL_RUN_ID", allow_hyphen=False)
    prefix = re.sub(r"[^A-Za-z0-9_]+", "_", env_str("MODEL_RUN_ID_PREFIX", "weekly_clustering")).strip("_")
    prefix = prefix or "weekly_clustering"
    suffix = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return safe_identifier(f"{prefix}_{suffix}", "generated model_run_id", allow_hyphen=False)


def table_id(project_id: str, dataset: str, table_name: str) -> str:
    return f"{project_id}.{dataset}.{table_name}"


def import_serving_helpers() -> dict[str, Any]:
    sys.path.insert(0, str(SERVING_DIR))
    from step_1_load_cluster_outputs import (  # type: ignore[import-not-found]
        ASSIGNMENTS_SCHEMA,
        NEIGHBORS_SCHEMA,
        PROFILES_SCHEMA,
        create_assignments_sql,
        create_neighbors_sql,
        create_profiles_sql,
    )
    from step_2_build_cluster_event_affinity import build_sql as build_affinity_sql  # type: ignore[import-not-found]
    from step_3_generate_user_recommendation_candidates import build_sql as build_candidates_sql  # type: ignore[import-not-found]
    from step_4_validate_serving_outputs import counts_sql  # type: ignore[import-not-found]

    return {
        "ASSIGNMENTS_SCHEMA": ASSIGNMENTS_SCHEMA,
        "PROFILES_SCHEMA": PROFILES_SCHEMA,
        "NEIGHBORS_SCHEMA": NEIGHBORS_SCHEMA,
        "create_assignments_sql": create_assignments_sql,
        "create_profiles_sql": create_profiles_sql,
        "create_neighbors_sql": create_neighbors_sql,
        "build_affinity_sql": build_affinity_sql,
        "build_candidates_sql": build_candidates_sql,
        "counts_sql": counts_sql,
    }


def run_query(client: bigquery.Client, sql: str, label: str) -> None:
    log("query_started", label=label)
    client.query(sql).result()
    log("query_completed", label=label)


def export_feature_table_to_csv(
    client: bigquery.Client,
    source_table: str,
    destination: Path,
    min_swipes_30d: int,
    min_swipes_90d: int,
) -> int:
    query = f"""
select *
from `{source_table}`
where coalesce(total_swipes_30d, 0) >= @min_swipes_30d
  and coalesce(total_swipes_90d, 0) >= @min_swipes_90d
""".strip()
    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("min_swipes_30d", "INT64", min_swipes_30d),
            bigquery.ScalarQueryParameter("min_swipes_90d", "INT64", min_swipes_90d),
        ],
    )
    rows = list(client.query(query, job_config=job_config).result())
    if not rows:
        raise RuntimeError(
            f"No eligible users found in {source_table} with "
            f"min_swipes_30d={min_swipes_30d} and min_swipes_90d={min_swipes_90d}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row.items()))
    return len(rows)


def run_training(k_values: str) -> None:
    if not TRAINING_SCRIPT.exists():
        raise FileNotFoundError(f"Missing training script: {TRAINING_SCRIPT}")
    command = [
        sys.executable,
        str(TRAINING_SCRIPT),
        "--input-csv",
        str(FEATURE_EXPORT_CSV),
        "--output-dir",
        str(TRAINING_OUTPUT_DIR),
        "--k-values",
        k_values,
    ]
    log("training_started", command=" ".join(command))
    subprocess.run(command, check=True)
    log("training_completed", output_dir=str(TRAINING_OUTPUT_DIR))


def parse_schema(schema: str) -> list[bigquery.SchemaField]:
    fields = []
    for raw_field in schema.split(","):
        name, field_type = raw_field.split(":", 1)
        fields.append(bigquery.SchemaField(name.strip(), field_type.strip()))
    return fields


def load_csv_to_bigquery(
    client: bigquery.Client,
    destination_table: str,
    csv_path: Path,
    schema: str,
) -> None:
    if not csv_path.exists():
        raise FileNotFoundError(f"Missing CSV output: {csv_path}")
    job_config = bigquery.LoadJobConfig(
        schema=parse_schema(schema),
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )
    log("load_started", table=destination_table, csv=str(csv_path))
    with csv_path.open("rb") as handle:
        client.load_table_from_file(handle, destination_table, job_config=job_config).result()
    log("load_completed", table=destination_table)


def load_training_outputs(
    client: bigquery.Client,
    helpers: dict[str, Any],
    project_id: str,
    marts_dataset: str,
    run_id: str,
) -> list[str]:
    run_suffix = run_id.lower()
    tmp_assignments = f"_tmp_user_cluster_assignments_{run_suffix}"
    tmp_profiles = f"_tmp_cluster_profiles_{run_suffix}"
    tmp_neighbors = f"_tmp_cluster_neighbors_{run_suffix}"

    load_csv_to_bigquery(
        client,
        table_id(project_id, marts_dataset, tmp_assignments),
        TRAINING_OUTPUT_DIR / "user_cluster_assignments.csv",
        helpers["ASSIGNMENTS_SCHEMA"],
    )
    load_csv_to_bigquery(
        client,
        table_id(project_id, marts_dataset, tmp_profiles),
        TRAINING_OUTPUT_DIR / "cluster_profiles.csv",
        helpers["PROFILES_SCHEMA"],
    )
    load_csv_to_bigquery(
        client,
        table_id(project_id, marts_dataset, tmp_neighbors),
        TRAINING_OUTPUT_DIR / "cluster_neighbors.csv",
        helpers["NEIGHBORS_SCHEMA"],
    )

    run_query(
        client,
        helpers["create_assignments_sql"](project_id, marts_dataset, tmp_assignments, run_id),
        "create_user_cluster_assignments",
    )
    run_query(
        client,
        helpers["create_profiles_sql"](project_id, marts_dataset, tmp_profiles, run_id),
        "create_cluster_profiles",
    )
    run_query(
        client,
        helpers["create_neighbors_sql"](project_id, marts_dataset, tmp_neighbors, run_id),
        "create_cluster_neighbors",
    )
    return [
        table_id(project_id, marts_dataset, tmp_assignments),
        table_id(project_id, marts_dataset, tmp_profiles),
        table_id(project_id, marts_dataset, tmp_neighbors),
    ]


def cleanup_tables(client: bigquery.Client, tables: list[str]) -> None:
    for temp_table in tables:
        client.delete_table(temp_table, not_found_ok=True)
        log("temp_table_deleted", table=temp_table)


def validate_outputs(client: bigquery.Client, helpers: dict[str, Any], project_id: str, marts_dataset: str) -> None:
    rows = list(client.query(helpers["counts_sql"](project_id, marts_dataset)).result())
    if not rows:
        raise RuntimeError("Validation query returned no rows.")
    counts = dict(rows[0].items())
    log("serving_validation_counts", **counts)

    assigned_users = int(counts.get("assigned_users") or 0)
    users_with_recommendations = int(counts.get("users_with_recommendations") or 0)
    recommendation_rows = int(counts.get("recommendation_rows") or 0)
    if assigned_users <= 0:
        raise RuntimeError("No users were assigned to clusters.")
    if users_with_recommendations <= 0 or recommendation_rows <= 0:
        raise RuntimeError("No cluster recommendations were generated.")


def main() -> None:
    project_id = safe_identifier(os.environ["GCP_PROJECT"], "GCP_PROJECT")
    raw_dataset = safe_identifier(env_str("BQ_RAW_DATASET", "recomendacion_planes"), "BQ_RAW_DATASET")
    marts_dataset = safe_identifier(env_str("BQ_MARTS_DATASET", "recomendacion_planes_marts"), "BQ_MARTS_DATASET")
    feature_dataset = safe_identifier(env_str("BQ_FEATURE_DATASET", marts_dataset), "BQ_FEATURE_DATASET")
    feature_table = safe_identifier(env_str("BQ_SOURCE_FEATURE_TABLE", "dim_user_cluster_features_current"), "BQ_SOURCE_FEATURE_TABLE")
    bq_location = env_str("BQ_LOCATION", "EU")
    run_id = model_run_id()
    min_swipes_30d = env_int("MIN_SWIPES_30D", 8)
    min_swipes_90d = env_int("MIN_SWIPES_90D", 24)
    k_values = env_str("K_VALUES", "4,5,6,7,8")
    lookback_days = env_int("LOOKBACK_DAYS", 90)
    neighbor_count = env_int("NEIGHBOR_COUNT", 2)
    max_per_user = env_int("MAX_RECOMMENDATIONS_PER_USER", 30)

    helpers = import_serving_helpers()
    source_table = table_id(project_id, feature_dataset, feature_table)
    client = bigquery.Client(project=project_id, location=bq_location)

    log(
        "job_started",
        model_run_id=run_id,
        feature_table=source_table,
        raw_dataset=raw_dataset,
        marts_dataset=marts_dataset,
        bq_location=bq_location,
    )
    exported_rows = export_feature_table_to_csv(
        client,
        source_table,
        FEATURE_EXPORT_CSV,
        min_swipes_30d,
        min_swipes_90d,
    )
    log("feature_export_ready", path=str(FEATURE_EXPORT_CSV), rows=exported_rows)

    run_training(k_values)

    temp_tables = load_training_outputs(client, helpers, project_id, marts_dataset, run_id)
    run_query(
        client,
        helpers["build_affinity_sql"](project_id, marts_dataset, run_id, lookback_days),
        "create_cluster_event_affinity",
    )
    run_query(
        client,
        helpers["build_candidates_sql"](
            project_id,
            raw_dataset,
            marts_dataset,
            run_id,
            neighbor_count,
            max_per_user,
        ),
        "create_user_recommendation_candidates",
    )
    validate_outputs(client, helpers, project_id, marts_dataset)
    cleanup_tables(client, temp_tables)
    log("job_completed", model_run_id=run_id)


if __name__ == "__main__":
    main()
