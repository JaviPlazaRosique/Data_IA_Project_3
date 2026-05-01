from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

from google.cloud import bigquery


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parents[2]
LOCAL_WORKDIR = Path(os.environ.get("LOCAL_WORKDIR", "/tmp/clustering_job"))
FEATURE_EXPORT_CSV = LOCAL_WORKDIR / "dim_user_cluster_features_current.csv"
TRAINING_OUTPUT_DIR = LOCAL_WORKDIR / "training_outputs"


def log(event: str, **payload: object) -> None:
    print(json.dumps({"event": event, **payload}, ensure_ascii=True))


def export_feature_table_to_csv(client: bigquery.Client, table_fqdn: str, destination: Path) -> None:
    query = f"select * from `{table_fqdn}`"
    rows = list(client.query(query).result())
    if not rows:
        raise RuntimeError(f"No rows returned from {table_fqdn}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row.items()))


def main() -> None:
    project_id = os.environ["GCP_PROJECT"]
    source_dataset = os.environ["BQ_SOURCE_DATASET"]
    feature_table = os.environ["BQ_SOURCE_FEATURE_TABLE"]
    table_fqdn = f"{project_id}.{source_dataset}.{feature_table}"

    log("job_started", table=table_fqdn)
    client = bigquery.Client(project=project_id)
    export_feature_table_to_csv(client, table_fqdn, FEATURE_EXPORT_CSV)
    log("feature_export_ready", path=str(FEATURE_EXPORT_CSV))

    training_script = REPO_ROOT / "clustering" / "integracion_datos_reales_gcp" / "step_4_entrenar_desde_feature_export.py"
    subprocess.run(
        [
            sys.executable,
            str(training_script),
            "--input-csv",
            str(FEATURE_EXPORT_CSV),
            "--output-dir",
            str(TRAINING_OUTPUT_DIR),
        ],
        check=True,
    )
    log("training_completed", output_dir=str(TRAINING_OUTPUT_DIR))
    log(
        "next_step_required",
        message="Persist the CSV outputs back to BigQuery tables or load them to GCS/BigQuery in a follow-up iteration.",
    )


if __name__ == "__main__":
    main()
