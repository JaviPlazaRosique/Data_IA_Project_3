from __future__ import annotations

import argparse
import csv
from pathlib import Path

from demo_config import DEMO_USERS_PATH


DEFAULT_INPUT = Path(
    "clustering/2_integracion_datos_gcp/real_exports/"
    "dim_user_cluster_features_current_synthetic_demo_20260502.csv"
)
DEFAULT_OUTPUT = Path(
    "clustering/2_integracion_datos_gcp/real_exports/"
    "dim_user_cluster_features_current_synthetic_demo_20260502_enriched.csv"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Add local demo metadata to a feature export for clustering interpretation."
    )
    parser.add_argument("--input-csv", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--users-csv", type=Path, default=DEMO_USERS_PATH)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def main() -> None:
    args = parse_args()
    feature_rows = read_csv(args.input_csv)
    demo_users = read_csv(args.users_csv)
    metadata_by_user = {
        row["user_id"]: {
            "home_city": row.get("home_city", ""),
            "synthetic_persona": row.get("persona", ""),
        }
        for row in demo_users
    }

    enriched_rows: list[dict[str, str]] = []
    for row in feature_rows:
        metadata = metadata_by_user.get(row["user_id"], {"home_city": "", "synthetic_persona": ""})
        enriched = {
            "user_id": row["user_id"],
            "home_city": metadata["home_city"],
            "synthetic_persona": metadata["synthetic_persona"],
        }
        for key, value in row.items():
            if key != "user_id":
                enriched[key] = value
        enriched_rows.append(enriched)

    fieldnames = list(enriched_rows[0].keys()) if enriched_rows else ["user_id", "home_city", "synthetic_persona"]
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    matched = sum(1 for row in enriched_rows if row["synthetic_persona"])
    print(f"Enriched {matched}/{len(enriched_rows)} feature rows with demo metadata")
    print(f"Output CSV: {args.output_csv}")


if __name__ == "__main__":
    main()
