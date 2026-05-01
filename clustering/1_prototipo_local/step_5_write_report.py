from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "output"
ARTIFACTS_DIR = BASE_DIR / "artifacts"

USERS_PATH = DATA_DIR / "synthetic_users.csv"
EVENTS_PATH = DATA_DIR / "synthetic_events_catalog.csv"
INTERACTIONS_PATH = DATA_DIR / "synthetic_fct_swipes.csv"
CLUSTER_PROFILES_PATH = OUTPUT_DIR / "cluster_profiles.csv"
CLUSTER_NEIGHBORS_PATH = OUTPUT_DIR / "cluster_neighbors.csv"
MODEL_METRICS_PATH = OUTPUT_DIR / "model_selection_metrics.csv"
REPORT_PATH = OUTPUT_DIR / "prototype_report.md"
MODEL_ARTIFACTS_PATH = ARTIFACTS_DIR / "model_artifacts.json"

ANCHOR_DATE = date(2026, 4, 30)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required file: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str) -> bool:
    return value.lower() == "true"


def load_users() -> list[dict[str, Any]]:
    return read_csv_rows(USERS_PATH)


def load_events() -> list[dict[str, Any]]:
    rows = read_csv_rows(EVENTS_PATH)
    events: list[dict[str, Any]] = []
    for row in rows:
        events.append(
            {
                **row,
                "precio_min": float(row["precio_min"]),
                "precio_max": float(row["precio_max"]),
                "fecha_evento": date.fromisoformat(row["fecha_evento"]),
            }
        )
    return events


def load_interactions() -> list[dict[str, Any]]:
    rows = read_csv_rows(INTERACTIONS_PATH)
    interactions: list[dict[str, Any]] = []
    for row in rows:
        interactions.append(
            {
                **row,
                "event_timestamp": datetime.fromisoformat(row["event_timestamp"]),
                "liked": parse_bool(row["liked"]),
                "price_mid": float(row["price_mid"]),
            }
        )
    return interactions


def load_cluster_profiles() -> list[dict[str, Any]]:
    rows = read_csv_rows(CLUSTER_PROFILES_PATH)
    profiles: list[dict[str, Any]] = []
    float_fields = {
        "share_of_users",
        "dominant_synthetic_persona_share",
        "dominant_home_city_share",
        "avg_total_swipes_90d",
        "avg_right_swipe_rate_90d",
        "avg_local_like_rate_90d",
        "avg_chat_swipe_share_90d",
        "avg_days_until_event_liked_90d",
        "avg_price_mid_liked_90d",
    }
    for row in rows:
        parsed: dict[str, Any] = {}
        for key, value in row.items():
            if key in {"cluster_id", "cluster_size"}:
                parsed[key] = int(value)
            elif key in float_fields:
                parsed[key] = float(value)
            else:
                parsed[key] = value
        profiles.append(parsed)
    return profiles


def load_cluster_neighbors() -> list[dict[str, Any]]:
    rows = read_csv_rows(CLUSTER_NEIGHBORS_PATH)
    neighbors: list[dict[str, Any]] = []
    for row in rows:
        neighbors.append(
            {
                "cluster_id": int(row["cluster_id"]),
                "neighbor_rank": int(row["neighbor_rank"]),
                "neighbor_cluster_id": int(row["neighbor_cluster_id"]),
                "euclidean_distance": float(row["euclidean_distance"]),
                "cosine_similarity": float(row["cosine_similarity"]),
            }
        )
    return neighbors


def load_model_metrics() -> list[dict[str, Any]]:
    rows = read_csv_rows(MODEL_METRICS_PATH)
    metrics: list[dict[str, Any]] = []
    for row in rows:
        metrics.append(
            {
                "k": int(row["k"]),
                "inertia": float(row["inertia"]),
                "silhouette_score": float(row["silhouette_score"]),
                "davies_bouldin_score": float(row["davies_bouldin_score"]),
                "min_cluster_size": int(row["min_cluster_size"]),
                "max_cluster_size": int(row["max_cluster_size"]),
                "mean_cluster_size": float(row["mean_cluster_size"]),
            }
        )
    return metrics


def weighted_cluster_purity(profiles: list[dict[str, Any]]) -> float:
    numerator = sum(float(profile["cluster_size"]) * float(profile["dominant_synthetic_persona_share"]) for profile in profiles)
    denominator = sum(float(profile["cluster_size"]) for profile in profiles)
    return numerator / denominator if denominator else 0.0


def build_report(
    users: list[dict[str, Any]],
    events: list[dict[str, Any]],
    interactions: list[dict[str, Any]],
    model_metrics: list[dict[str, Any]],
    best_model: dict[str, Any],
    profiles: list[dict[str, Any]],
    neighbors: list[dict[str, Any]],
) -> str:
    chosen_k = int(best_model["k"])
    chosen_metrics = best_model["metrics"]
    purity = weighted_cluster_purity(profiles)
    lines: list[str] = []
    lines.append("# Informe del prototipo local")
    lines.append("")
    lines.append("## Resumen")
    lines.append(f"- Fecha de corte: {ANCHOR_DATE.isoformat()}")
    lines.append(f"- Usuarios sinteticos: {len(users)}")
    lines.append(f"- Eventos sinteticos: {len(events)}")
    lines.append(f"- Interacciones sinteticas: {len(interactions)}")
    lines.append("- Ventanas de features: 30 dias y 90 dias")
    lines.append("- Baseline: estandarizacion manual + KMeans implementado en Python estandar")
    lines.append("")
    lines.append("## Seleccion de k")
    lines.append("")
    lines.append("| k | silhouette | davies_bouldin | min_cluster_size | max_cluster_size |")
    lines.append("| --- | --- | --- | --- | --- |")
    for metric in sorted(model_metrics, key=lambda row: int(row["k"])):
        lines.append(
            f"| {metric['k']} | {metric['silhouette_score']:.4f} | {metric['davies_bouldin_score']:.4f} | {metric['min_cluster_size']} | {metric['max_cluster_size']} |"
        )
    lines.append("")
    lines.append(
        f"Se selecciono `k = {chosen_k}` porque ofrece el mejor equilibrio entre separacion (`silhouette = {chosen_metrics['silhouette_score']:.4f}`), compacidad (`davies_bouldin = {chosen_metrics['davies_bouldin_score']:.4f}`) y tamano minimo de cluster (`{chosen_metrics['min_cluster_size']}` usuarios)."
    )
    lines.append("")
    lines.append("## Lectura de clusters")
    lines.append("")
    for profile in sorted(profiles, key=lambda row: int(row["cluster_id"])):
        lines.append(
            "- "
            f"Cluster {profile['cluster_id']}: {profile['cluster_size']} usuarios, "
            f"persona dominante `{profile['dominant_synthetic_persona']}` ({float(profile['dominant_synthetic_persona_share']):.0%}), "
            f"segmentos top `{profile['top_segment_1']}` y `{profile['top_segment_2']}`, "
            f"generos top `{profile['top_genre_1']}` y `{profile['top_genre_2']}`, "
            f"right_swipe_rate_90d medio `{float(profile['avg_right_swipe_rate_90d']):.2f}`."
        )
    lines.append("")
    lines.append("## Clusters cercanos")
    lines.append("")
    nearest_by_cluster: dict[int, dict[str, Any]] = {}
    for row in neighbors:
        if int(row["neighbor_rank"]) == 1:
            nearest_by_cluster[int(row["cluster_id"])] = row
    for cluster_id in sorted(nearest_by_cluster):
        row = nearest_by_cluster[cluster_id]
        lines.append(
            "- "
            f"Cluster {cluster_id} -> cluster {row['neighbor_cluster_id']} "
            f"(distancia euclidea {float(row['euclidean_distance']):.3f}, similitud coseno {float(row['cosine_similarity']):.3f})."
        )
    lines.append("")
    lines.append("## Conclusion")
    lines.append("")
    lines.append(
        f"La pureza ponderada frente a las personas sinteticas es `{purity:.2%}`, lo que indica que el baseline recupera grupos de gusto reconocibles en este entorno controlado."
    )
    lines.append(
        "El prototipo es interpretable porque los clusters quedan definidos por tasas de like por segmento y genero, comportamiento local vs viaje, sensibilidad al precio y horizonte temporal del evento."
    )
    lines.append(
        "Tambien es util para producto: ya permite recomendar primero eventos alineados con el cluster del usuario y despues ampliar con los clusters vecinos mejor posicionados."
    )
    lines.append(
        "Antes de llevarlo a produccion conviene sustituir la senal sintetica por features derivadas de `fct_swipes`, reforzar los precios en el mart y validar el impacto sobre recomendaciones reales."
    )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    users = load_users()
    events = load_events()
    interactions = load_interactions()
    profiles = load_cluster_profiles()
    neighbors = load_cluster_neighbors()
    model_metrics = load_model_metrics()
    model_artifacts = read_json(MODEL_ARTIFACTS_PATH)
    best_model = {
        "k": int(model_artifacts["selected_k"]),
        "metrics": {
            "k": int(model_artifacts["selected_metrics"]["k"]),
            "inertia": float(model_artifacts["selected_metrics"]["inertia"]),
            "silhouette_score": float(model_artifacts["selected_metrics"]["silhouette_score"]),
            "davies_bouldin_score": float(model_artifacts["selected_metrics"]["davies_bouldin_score"]),
            "min_cluster_size": int(model_artifacts["selected_metrics"]["min_cluster_size"]),
            "max_cluster_size": int(model_artifacts["selected_metrics"]["max_cluster_size"]),
            "mean_cluster_size": float(model_artifacts["selected_metrics"]["mean_cluster_size"]),
        },
    }
    REPORT_PATH.write_text(
        build_report(users, events, interactions, model_metrics, best_model, profiles, neighbors),
        encoding="utf-8",
    )
    print("Step 5 completed: final report written.")
    print(f"Selected k: {best_model['k']}")
    print(f"Clusters: {len(profiles)}")
    print(f"Report path: {REPORT_PATH}")


if __name__ == "__main__":
    main()
