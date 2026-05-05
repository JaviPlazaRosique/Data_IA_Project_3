from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
PROTOTYPE_FEATURES_PATH = BASE_DIR.parent / "prototipo_local" / "output" / "user_features.csv"

SEGMENTS = ["Music", "Sports", "Arts_Theatre", "Family"]
GENRES = [
    "Rock",
    "Pop",
    "Electronic",
    "Urban",
    "Football",
    "Basketball",
    "Tennis",
    "Theatre",
    "Musical",
    "Comedy",
    "Classical",
    "Kids",
    "Circus",
    "Exhibition",
]


def slugify(value: str) -> str:
    return value.lower().replace("&", "and").replace(" ", "_")


def prototype_feature_names() -> list[str]:
    base_features = []
    for window in ("30d", "90d"):
        base_features.extend(
            [
                f"total_swipes_{window}",
                f"total_right_swipes_{window}",
                f"right_swipe_rate_{window}",
                f"avg_dwell_ms_{window}",
                f"avg_right_dwell_ms_{window}",
                f"distinct_segments_liked_{window}",
                f"distinct_genres_liked_{window}",
                f"distinct_cities_liked_{window}",
                f"local_like_rate_{window}",
                f"local_swipe_share_{window}",
                f"avg_days_until_event_liked_{window}",
                f"avg_price_mid_liked_{window}",
                f"median_price_mid_liked_{window}",
                f"avg_price_mid_disliked_{window}",
                f"chat_swipe_share_{window}",
                f"chat_right_rate_{window}",
                f"days_since_last_right_swipe_{window}",
            ]
        )
        base_features.extend([f"like_rate_segment_{slugify(segment)}_{window}" for segment in SEGMENTS])
        base_features.extend([f"like_rate_genre_{slugify(genre)}_{window}" for genre in GENRES])
    base_features.extend(
        [
            "right_swipe_rate_delta_30_vs_90",
            "total_swipes_delta_30_vs_90",
        ]
    )
    return base_features


def load_feature_columns() -> list[str]:
    if not PROTOTYPE_FEATURES_PATH.exists():
        return prototype_feature_names()
    with PROTOTYPE_FEATURES_PATH.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.reader(handle)
        header = next(reader)
    return [column for column in header if column not in {"user_id", "home_city", "synthetic_persona"}]


def classify_feature(feature_name: str) -> dict[str, str]:
    if feature_name in {"right_swipe_rate_delta_30_vs_90", "total_swipes_delta_30_vs_90"}:
        return {
            "status": "derived_after_feature_models",
            "source_table": "dim_user_cluster_features_current",
            "source_columns": "int_user_swipe_features_30d + int_user_swipe_features_90d",
            "blocking_reason": "",
            "proposed_expression": "difference between 30d and 90d aggregated features",
        }

    if feature_name.startswith("avg_dwell_ms_") or feature_name.startswith("avg_right_dwell_ms_"):
        return {
            "status": "needs_staging_enrichment",
            "source_table": "raw.swipes_raw -> stg_swipes -> fct_swipes",
            "source_columns": "data.dwell_ms",
            "blocking_reason": "The raw payload already includes dwell_ms, but stg_swipes and fct_swipes do not expose it yet.",
            "proposed_expression": "avg(dwell_ms) or avg(if(liked, dwell_ms, null))",
        }

    if feature_name.startswith("local_like_rate_") or feature_name.startswith("local_swipe_share_"):
        return {
            "status": "needs_user_profile_join",
            "source_table": "fct_swipes + user profile source",
            "source_columns": "ciudad + user preferred/home city",
            "blocking_reason": "The event city exists, but the analytical model does not currently have the user's home/preferred city joined in.",
            "proposed_expression": "compare event ciudad against user preferred/home city",
        }

    if "price_mid" in feature_name:
        return {
            "status": "needs_event_price_enrichment",
            "source_table": "catalog.eventos -> fct_swipes",
            "source_columns": "precio_min, precio_max or banda_precio",
            "blocking_reason": "fct_swipes currently sets precio_min and precio_max to null for all rows.",
            "proposed_expression": "avg((precio_min + precio_max) / 2) or a band-based proxy",
        }

    if feature_name.startswith("median_price_mid_"):
        return {
            "status": "needs_event_price_enrichment",
            "source_table": "catalog.eventos -> fct_swipes",
            "source_columns": "precio_min, precio_max or banda_precio",
            "blocking_reason": "Median price needs event price values, which are not yet present in fct_swipes.",
            "proposed_expression": "approx_quantiles(price_mid, 2)[offset(1)]",
        }

    if feature_name.startswith("avg_days_until_event_liked_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "event_timestamp, fecha_evento, liked",
            "blocking_reason": "",
            "proposed_expression": "avg(if(liked, date_diff(fecha_evento, date(event_timestamp), day), null))",
        }

    if feature_name.startswith("chat_swipe_share_") or feature_name.startswith("chat_right_rate_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "recommendation_context, liked",
            "blocking_reason": "",
            "proposed_expression": "share of chat interactions or likes inside chat context",
        }

    if feature_name.startswith("days_since_last_right_swipe_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "event_timestamp, liked",
            "blocking_reason": "",
            "proposed_expression": "timestamp_diff(current_timestamp(), max(if(liked, event_timestamp, null)), day)",
        }

    if feature_name.startswith("like_rate_segment_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "segmento, liked",
            "blocking_reason": "",
            "proposed_expression": "coalesce(safe_divide(countif(liked and segmento = X), countif(segmento = X)), 0.0)",
        }

    if feature_name.startswith("like_rate_genre_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "genero, liked",
            "blocking_reason": "",
            "proposed_expression": "coalesce(safe_divide(countif(liked and genero = X), countif(genero = X)), 0.0)",
        }

    if feature_name.startswith("distinct_segments_liked_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "segmento, liked",
            "blocking_reason": "",
            "proposed_expression": "count(distinct if(liked, segmento, null))",
        }

    if feature_name.startswith("distinct_genres_liked_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "genero, liked",
            "blocking_reason": "",
            "proposed_expression": "count(distinct if(liked, genero, null))",
        }

    if feature_name.startswith("distinct_cities_liked_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "ciudad, liked",
            "blocking_reason": "",
            "proposed_expression": "count(distinct if(liked, ciudad, null))",
        }

    if feature_name.startswith("total_swipes_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "user_id, event_timestamp",
            "blocking_reason": "",
            "proposed_expression": "count(*)",
        }

    if feature_name.startswith("total_right_swipes_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "liked",
            "blocking_reason": "",
            "proposed_expression": "countif(liked)",
        }

    if feature_name.startswith("right_swipe_rate_"):
        return {
            "status": "available_now",
            "source_table": "fct_swipes",
            "source_columns": "liked",
            "blocking_reason": "",
            "proposed_expression": "safe_divide(countif(liked), count(*))",
        }

    return {
        "status": "available_now",
        "source_table": "fct_swipes",
        "source_columns": "multiple analytical columns",
        "blocking_reason": "",
        "proposed_expression": "implemented directly from fct_swipes aggregations",
    }


def write_mapping_csv(rows: list[dict[str, str]]) -> Path:
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUTS_DIR / "feature_mapping.csv"
    fieldnames = [
        "prototype_feature",
        "status",
        "source_table",
        "source_columns",
        "blocking_reason",
        "proposed_expression",
    ]
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def write_gap_report(rows: list[dict[str, str]]) -> Path:
    report_path = OUTPUTS_DIR / "feature_gap_report.md"
    counts = Counter(row["status"] for row in rows)
    immediate_next_steps = [
        "Exponer `dwell_ms` en `stg_swipes` y `fct_swipes` para desbloquear engagement real.",
        "Enriquecer `fct_swipes` con precio numerico o, como minimo, con `banda_precio` procedente del catalogo.",
        "Definir como se obtiene la ciudad de referencia del usuario para calcular features locales.",
        "Crear los modelos dbt de 30 y 90 dias para materializar estas features de forma estable.",
    ]

    lines = [
        "# Gap report entre el prototipo y `fct_swipes`",
        "",
        "## Resumen",
        "",
        f"- Total de features revisadas: {len(rows)}",
        f"- Disponibles ya en `fct_swipes`: {counts.get('available_now', 0)}",
        f"- Requieren join con perfil de usuario: {counts.get('needs_user_profile_join', 0)}",
        f"- Requieren enriquecer staging o marts: {counts.get('needs_staging_enrichment', 0)}",
        f"- Requieren enriquecer precio del evento: {counts.get('needs_event_price_enrichment', 0)}",
        f"- Se derivan despues de construir tablas de 30d/90d: {counts.get('derived_after_feature_models', 0)}",
        "",
        "## Lectura principal",
        "",
        "La mayor parte de las features de comportamiento y afinidad por contenido ya se pueden construir sobre `fct_swipes`.",
        "Los bloqueos mas importantes estan en tres sitios: `dwell_ms`, precio del evento y contexto geografico del usuario.",
        "Esto significa que el siguiente paso correcto no es mover el job a GCP, sino materializar primero las features reales en dbt.",
        "",
        "## Siguientes acciones recomendadas",
        "",
    ]
    lines.extend([f"- {item}" for item in immediate_next_steps])
    lines.append("")
    lines.append("## Nota sobre precio")
    lines.append("")
    lines.append(
        "El catalogo ya maneja `banda_precio` en ingestión. Si el precio numerico tarda en llegar a `fct_swipes`, esa banda puede servir como proxy temporal."
    )
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main() -> None:
    feature_rows = []
    for feature_name in load_feature_columns():
        mapping = classify_feature(feature_name)
        feature_rows.append({"prototype_feature": feature_name, **mapping})
    csv_path = write_mapping_csv(feature_rows)
    report_path = write_gap_report(feature_rows)
    print("Step 1 completed: feature mapping against real data created.")
    print(f"Mapped features: {len(feature_rows)}")
    print(f"CSV mapping: {csv_path}")
    print(f"Gap report: {report_path}")


if __name__ == "__main__":
    main()
