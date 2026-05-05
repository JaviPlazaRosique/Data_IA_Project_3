from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "outputs"

DEFAULT_PROJECT_ID = "project3grupo3"
DEFAULT_RAW_DATASET = "recomendacion_planes"
DEFAULT_MARTS_DATASET = "recomendacion_planes_marts"
DEFAULT_MODEL_RUN_ID = "smoke_synthetic_demo_improved_20260502"
DEFAULT_LOOKBACK_DAYS = 90
DEFAULT_NEIGHBOR_COUNT = 2
DEFAULT_MAX_RECOMMENDATIONS_PER_USER = 30

DEFAULT_TRAINING_OUTPUT_DIR = (
    BASE_DIR.parent
    / "2_integracion_datos_gcp"
    / "training_outputs"
    / "smoke_synthetic_demo_improved_20260502_all_users"
)

VALIDATION_SUMMARY_PATH = OUTPUT_DIR / "serving_validation_summary.json"


def ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def safe_sql_literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def table(project_id: str, dataset: str, table_name: str) -> str:
    return f"`{project_id}.{dataset}.{table_name}`"
