from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

STEP_SCRIPTS = [
    "step_1_generate_synthetic_data.py",
    "step_2_build_user_features.py",
    "step_3_train_baseline_model.py",
    "step_4_build_cluster_outputs.py",
    "step_5_write_report.py",
]


def main() -> None:
    print("Starting prototype pipeline.", flush=True)
    for script_name in STEP_SCRIPTS:
        script_path = BASE_DIR / script_name
        print(f"Running {script_name}...", flush=True)
        subprocess.run([sys.executable, str(script_path)], check=True)
    print("Prototype generated successfully.", flush=True)


if __name__ == "__main__":
    main()
