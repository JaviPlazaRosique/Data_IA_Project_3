from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from serving_config import (
    DEFAULT_LOOKBACK_DAYS,
    DEFAULT_MAX_RECOMMENDATIONS_PER_USER,
    DEFAULT_MODEL_RUN_ID,
    DEFAULT_NEIGHBOR_COUNT,
    DEFAULT_PROJECT_ID,
    DEFAULT_TRAINING_OUTPUT_DIR,
)


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run cluster recommendation serving pipeline.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--training-output-dir", type=Path, default=DEFAULT_TRAINING_OUTPUT_DIR)
    parser.add_argument("--model-run-id", default=DEFAULT_MODEL_RUN_ID)
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--neighbor-count", type=int, default=DEFAULT_NEIGHBOR_COUNT)
    parser.add_argument("--max-per-user", type=int, default=DEFAULT_MAX_RECOMMENDATIONS_PER_USER)
    return parser.parse_args()


def run_step(script_name: str, extra_args: list[str]) -> None:
    command = [sys.executable, str(BASE_DIR / script_name), *extra_args]
    print(f"\nRunning {script_name}")
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()

    run_step(
        "step_1_load_cluster_outputs.py",
        [
            "--project-id",
            args.project_id,
            "--training-output-dir",
            str(args.training_output_dir),
            "--model-run-id",
            args.model_run_id,
        ],
    )
    run_step(
        "step_2_build_cluster_event_affinity.py",
        [
            "--project-id",
            args.project_id,
            "--model-run-id",
            args.model_run_id,
            "--lookback-days",
            str(args.lookback_days),
        ],
    )
    run_step(
        "step_3_generate_user_recommendation_candidates.py",
        [
            "--project-id",
            args.project_id,
            "--model-run-id",
            args.model_run_id,
            "--neighbor-count",
            str(args.neighbor_count),
            "--max-per-user",
            str(args.max_per_user),
        ],
    )
    run_step("step_4_validate_serving_outputs.py", ["--project-id", args.project_id])


if __name__ == "__main__":
    main()
