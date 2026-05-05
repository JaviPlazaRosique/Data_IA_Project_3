from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from demo_config import DEFAULT_ANCHOR_DATE, DEFAULT_PROJECT_ID, DEFAULT_RUN_ID, DEFAULT_SEED


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the synthetic demo interactions pipeline.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--run-id", default=DEFAULT_RUN_ID)
    parser.add_argument("--anchor-date", default=DEFAULT_ANCHOR_DATE.isoformat())
    parser.add_argument(
        "--load-to-bigquery",
        action="store_true",
        help="Append generated rows to BigQuery swipes_raw and validate the load.",
    )
    parser.add_argument(
        "--force-load",
        action="store_true",
        help="Pass --force to the load step if the same run_id already exists.",
    )
    return parser.parse_args()


def run_step(script_name: str, extra_args: list[str]) -> None:
    command = [sys.executable, str(BASE_DIR / script_name), *extra_args]
    print(f"\nRunning {script_name}")
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()

    run_step("step_1_export_real_events.py", ["--project-id", args.project_id])
    run_step("step_2_generate_demo_users.py", ["--seed", str(args.seed)])
    run_step(
        "step_3_generate_synthetic_swipes.py",
        [
            "--project-id",
            args.project_id,
            "--seed",
            str(args.seed),
            "--run-id",
            args.run_id,
            "--anchor-date",
            args.anchor_date,
        ],
    )

    if args.load_to_bigquery:
        load_args = ["--project-id", args.project_id]
        if args.force_load:
            load_args.append("--force")
        run_step("step_4_load_swipes_to_bigquery.py", load_args)
        run_step("step_5_validate_loaded_swipes.py", ["--project-id", args.project_id, "--run-id", args.run_id])
    else:
        print("\nGenerated local files only. Re-run with --load-to-bigquery to append rows to swipes_raw.")


if __name__ == "__main__":
    main()
