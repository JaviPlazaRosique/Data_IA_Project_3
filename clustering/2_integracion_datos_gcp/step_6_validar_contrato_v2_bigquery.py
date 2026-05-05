from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import Any


DEFAULT_PROJECT = "project3grupo3"
DEFAULT_DATASET = "recomendacion_planes"
DEFAULT_TABLE = "swipes_raw"


def run_bq_query(project_id: str, sql: str) -> list[dict[str, Any]]:
    command = [
        "bq",
        "query",
        f"--project_id={project_id}",
        "--use_legacy_sql=false",
        "--format=json",
        sql,
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def as_int(row: dict[str, Any], key: str) -> int:
    return int(row.get(key) or 0)


def pct(part: int, total: int) -> float:
    return round((part / total) * 100, 2) if total else 0.0


def build_contract_query(project_id: str, dataset: str, table: str, lookback_hours: int) -> str:
    table_fqdn = f"`{project_id}.{dataset}.{table}`"
    return f"""
select
  count(*) as total_rows,
  countif(json_value(data, '$.schema_version') = '2.0') as v2_rows,
  countif(json_value(data, '$.event_snapshot.event_id') is not null) as rows_with_event_snapshot,
  countif(json_value(data, '$.producer.surface') is not null) as rows_with_producer,
  countif(safe_cast(json_value(data, '$.rank_position') as int64) is not null) as rows_with_rank_position,
  countif(safe_cast(json_value(data, '$.dwell_ms') as int64) is not null) as rows_with_dwell_ms,
  countif(json_value(data, '$.event_snapshot.banda_precio') is not null) as rows_with_snapshot_banda_precio,
  countif(
    json_value(data, '$.event_snapshot.precio_min') is not null
    or json_value(data, '$.event_snapshot.precio_max') is not null
  ) as rows_with_snapshot_numeric_price,
  max(publish_time) as latest_publish_time
from {table_fqdn}
where publish_time >= timestamp_sub(current_timestamp(), interval {lookback_hours} hour)
"""


def build_price_proxy_query(project_id: str) -> str:
    return f"""
select
  count(*) as fct_rows,
  countif(banda_precio is not null) as rows_with_banda_precio,
  countif(banda_precio_score is not null) as rows_with_banda_precio_score,
  countif(price_proxy_mid is not null) as rows_with_price_proxy_mid,
  countif(precio_min is not null or precio_max is not null) as rows_with_numeric_price
from `{project_id}.recomendacion_planes_marts.fct_swipes`
"""


def print_metric(label: str, value: int, total: int) -> None:
    print(f"- {label}: {value}/{total} ({pct(value, total)}%)")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate swipe_event_contract_v2 in BigQuery.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--lookback-hours", type=int, default=24)
    parser.add_argument("--min-v2-rows", type=int, default=1)
    parser.add_argument("--skip-price-proxy-check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contract_rows = run_bq_query(
        args.project_id,
        build_contract_query(args.project_id, args.dataset, args.table, args.lookback_hours),
    )
    contract = contract_rows[0] if contract_rows else {}
    total_rows = as_int(contract, "total_rows")
    v2_rows = as_int(contract, "v2_rows")

    print("Contrato swipe_event_contract_v2")
    print(f"- Ventana: ultimas {args.lookback_hours} horas")
    print(f"- Filas raw: {total_rows}")
    print(f"- Ultimo publish_time: {contract.get('latest_publish_time') or 'n/a'}")
    print_metric("schema_version = 2.0", v2_rows, total_rows)
    print_metric("event_snapshot", as_int(contract, "rows_with_event_snapshot"), total_rows)
    print_metric("producer", as_int(contract, "rows_with_producer"), total_rows)
    print_metric("rank_position", as_int(contract, "rows_with_rank_position"), total_rows)
    print_metric("dwell_ms", as_int(contract, "rows_with_dwell_ms"), total_rows)
    print_metric("snapshot.banda_precio", as_int(contract, "rows_with_snapshot_banda_precio"), total_rows)
    print_metric("snapshot.precio_min/precio_max", as_int(contract, "rows_with_snapshot_numeric_price"), total_rows)

    if not args.skip_price_proxy_check:
        price_rows = run_bq_query(args.project_id, build_price_proxy_query(args.project_id))
        price = price_rows[0] if price_rows else {}
        fct_rows = as_int(price, "fct_rows")
        print("\nProxy de precio en fct_swipes")
        print_metric("banda_precio", as_int(price, "rows_with_banda_precio"), fct_rows)
        print_metric("banda_precio_score", as_int(price, "rows_with_banda_precio_score"), fct_rows)
        print_metric("price_proxy_mid", as_int(price, "rows_with_price_proxy_mid"), fct_rows)
        print_metric("precio_min/precio_max real", as_int(price, "rows_with_numeric_price"), fct_rows)

    if v2_rows < args.min_v2_rows:
        print(
            f"\nERROR: v2_rows={v2_rows}, por debajo del minimo requerido {args.min_v2_rows}.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
