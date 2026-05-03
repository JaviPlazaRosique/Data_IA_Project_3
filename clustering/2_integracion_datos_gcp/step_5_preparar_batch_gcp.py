from __future__ import annotations

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
GCP_BATCH_DIR = BASE_DIR / "gcp_batch"

REQUIRED_ASSETS = [
    "Dockerfile",
    "requirements.txt",
    "job_main.py",
    "cloud_run_job.env.example",
    "terraform_clustering_job_snippet.tf",
    "runbook.md",
]


def main() -> None:
    missing = [asset for asset in REQUIRED_ASSETS if not (GCP_BATCH_DIR / asset).exists()]
    if missing:
        formatted = ", ".join(missing)
        raise FileNotFoundError(f"Missing GCP batch assets in {GCP_BATCH_DIR}: {formatted}")

    print("Step 5 completed: GCP batch assets are ready.")
    print(f"GCP assets directory: {GCP_BATCH_DIR}")
    for asset in REQUIRED_ASSETS:
        print(f"- {asset}")


if __name__ == "__main__":
    main()
