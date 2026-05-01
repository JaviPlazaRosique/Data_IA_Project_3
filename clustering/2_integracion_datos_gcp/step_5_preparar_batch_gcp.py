from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
GCP_BATCH_DIR = BASE_DIR / "gcp_batch"


DOCKERFILE = """FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY clustering/integracion_datos_reales_gcp/gcp_batch/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app

ENTRYPOINT ["python", "clustering/integracion_datos_reales_gcp/gcp_batch/job_main.py"]
"""


REQUIREMENTS = """google-cloud-bigquery==3.41.0
"""


JOB_MAIN = """from __future__ import annotations

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
"""


ENV_EXAMPLE = """GCP_PROJECT=your-project-id
BQ_SOURCE_DATASET=recomendacion_planes
BQ_SOURCE_FEATURE_TABLE=dim_user_cluster_features_current
LOCAL_WORKDIR=/tmp/clustering_job
"""


TERRAFORM_SNIPPET = """module "clustering_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "clustering-train-sa"
  nombre_despliege   = "Cuenta de servicio para el job de clustering"
  cuenta_servicio_roles = [
    "roles/bigquery.dataViewer",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataEditor",
    "roles/storage.objectAdmin",
  ]
}

module "clustering_train_assign_job" {
  source                = "./modules/cloud_run_job"
  id_proyecto           = var.id_proyecto
  region                = var.region
  nombre_job            = "clustering-train-assign"
  nombre_repo_artifact  = module.repo_artifact.id_repo_artifact
  nombre_imagen         = "clustering-train-assign"
  ruta_contexto_docker  = "${path.root}/.."
  email_cuenta_servicio = module.clustering_sa.email_cuenta_servicio

  cpu     = "1"
  memoria = "2Gi"

  variables_entorno = {
    GCP_PROJECT            = var.id_proyecto
    BQ_SOURCE_DATASET      = module.bigquery.id_dataset
    BQ_SOURCE_FEATURE_TABLE = "dim_user_cluster_features_current"
    LOCAL_WORKDIR          = "/tmp/clustering_job"
  }
}

module "scheduler_clustering_sa" {
  source             = "./modules/iam"
  id_proyecto        = var.id_proyecto
  id_cuenta_servicio = "scheduler-clustering-sa"
  nombre_despliege   = "Cuenta de servicio para lanzar el job de clustering"
  cuenta_servicio_roles = [
    "roles/run.invoker"
  ]
}

module "scheduler_clustering_daily" {
  source       = "./modules/scheduler"
  id_proyecto  = var.id_proyecto
  region       = var.region
  nombre_job   = "clustering-train-assign-daily"
  descripcion  = "Lanza el Cloud Run Job de clustering una vez al dia"
  cron         = "0 2 * * *"
  zona_horaria = "Europe/Madrid"
  url_destino  = "https://${var.region}-run.googleapis.com/v2/projects/${var.id_proyecto}/locations/${var.region}/jobs/${module.clustering_train_assign_job.nombre_job}:run"
  metodo_http  = "POST"
  cabeceras    = { "Content-Type" = "application/json" }

  email_cuenta_servicio = module.scheduler_clustering_sa.email_cuenta_servicio
}
"""


RUNBOOK = """# Runbook del batch de clustering en GCP

## Objetivo

Ejecutar el entrenamiento del clustering como `Cloud Run Job`, leyendo la tabla de features reales desde BigQuery y generando salidas listas para su persistencia posterior.

## Orden recomendado

1. Materializar `dim_user_cluster_features_current` en BigQuery.
2. Construir y publicar la imagen del job.
3. Desplegar `Cloud Run Job` con una service account dedicada.
4. Probar una ejecucion manual.
5. Programar el job con `Cloud Scheduler`.

## Buenas practicas incluidas en este scaffold

- `Cloud Run Job` en lugar de servicio HTTP para batch puro.
- variables de entorno explicitas y separadas por responsabilidad.
- service account dedicada.
- logs estructurados en JSON.
- separacion entre dataset fuente y outputs locales del job.

## Siguientes mejoras recomendadas

- cargar `user_cluster_assignments`, `cluster_profiles` y `cluster_neighbors` de vuelta a BigQuery;
- versionar metricas y centroides en GCS;
- anadir alertas si el job falla o devuelve 0 usuarios;
- mover la lectura desde CSV temporal a persistencia directa en BigQuery para outputs finales.
"""


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    write_file(GCP_BATCH_DIR / "Dockerfile", DOCKERFILE)
    write_file(GCP_BATCH_DIR / "requirements.txt", REQUIREMENTS)
    write_file(GCP_BATCH_DIR / "job_main.py", JOB_MAIN)
    write_file(GCP_BATCH_DIR / "cloud_run_job.env.example", ENV_EXAMPLE)
    write_file(GCP_BATCH_DIR / "terraform_clustering_job_snippet.tf", TERRAFORM_SNIPPET)
    write_file(GCP_BATCH_DIR / "runbook.md", RUNBOOK)
    print("Step 5 completed: GCP batch assets prepared.")
    print(f"GCP assets directory: {GCP_BATCH_DIR}")


if __name__ == "__main__":
    main()
