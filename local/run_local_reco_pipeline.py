from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent
TRAINING_SCRIPT = REPO_ROOT / "clustering" / "2_integracion_datos_gcp" / "step_4_entrenar_desde_feature_export.py"

SWIPES_RAW_PATH = Path(os.environ.get("SWIPES_RAW_PATH", BASE_DIR / "swipes_data" / "swipes_raw.jsonl"))
EVENTS_CATALOG_PATH = Path(os.environ.get("EVENTS_CATALOG_PATH", BASE_DIR / "swipes_data" / "events_catalog.jsonl"))
OUTPUT_DIR = Path(os.environ.get("LOCAL_RECO_OUTPUT_DIR", BASE_DIR / "swipes_data" / "local_reco"))
RECOMMENDATIONS_OUTPUT_PATH = Path(
    os.environ.get("RECOMMENDATIONS_OUTPUT_PATH", BASE_DIR / "swipes_data" / "recommendations_local.csv")
)
MAX_RECOMMENDATIONS = int(os.environ.get("LOCAL_MAX_RECOMMENDATIONS_PER_USER", "10"))
K_VALUES = os.environ.get("LOCAL_K_VALUES", "2,3,4")

SEGMENTS = ["Music", "Sports", "Arts_Theatre", "Family", "Film"]
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
PRICE_BANDS = ["bajo", "medio", "alto"]
CSV_RECOMMENDATION_FIELDS = [
    "user_id",
    "event_id",
    "event_name",
    "fecha_evento",
    "ciudad",
    "recinto_nombre",
    "segmento",
    "genero",
    "subgenero",
    "recommendation_rank",
    "recommendation_score",
    "cluster_source",
]


def log(message: str) -> None:
    print(f"[local-reco] {message}", flush=True)


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def normalize_segment(value: str | None) -> str:
    if value in {"Music", "Sports", "Family", "Arts_Theatre", "Film"}:
        return value
    if value == "Arts & Theatre":
        return "Arts_Theatre"
    return value or "Unknown"


def normalize_genre(value: str | None, segment: str | None = None) -> str:
    if value in GENRES:
        return value
    lowered = (value or "").lower()
    if "electronic" in lowered or "techno" in lowered or "synth" in lowered:
        return "Electronic"
    if "soccer" in lowered or "football" in lowered:
        return "Football"
    if "flamenco" in lowered or "multimedia" in lowered or "sci-fi" in lowered:
        return "Theatre"
    if segment == "Family":
        return "Kids"
    return value or "Unknown"


def price_band(value: str | None) -> str:
    normalized = (value or "").strip().lower()
    return normalized if normalized in PRICE_BANDS else "medio"


def price_mid(event: dict[str, Any]) -> float:
    price_min = event.get("precio_min")
    price_max = event.get("precio_max")
    if isinstance(price_min, (int, float)) and isinstance(price_max, (int, float)):
        return (float(price_min) + float(price_max)) / 2.0
    return {"bajo": 15.0, "medio": 45.0, "alto": 90.0}.get(price_band(event.get("banda_precio")), 45.0)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise RuntimeError(f"Missing required input: {path}")
    rows = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def load_events() -> dict[str, dict[str, Any]]:
    events = {}
    for event in load_jsonl(EVENTS_CATALOG_PATH):
        event_id = str(event.get("id") or event.get("event_id") or "")
        if event_id:
            events[event_id] = event
    if not events:
        raise RuntimeError(f"No events found in {EVENTS_CATALOG_PATH}")
    return events


def load_swipes(events: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    seen_message_ids: set[str] = set()
    swipes = []
    for row in load_jsonl(SWIPES_RAW_PATH):
        message_id = str(row.get("message_id") or "")
        if message_id and message_id in seen_message_ids:
            continue
        if message_id:
            seen_message_ids.add(message_id)

        payload_raw = row.get("data")
        payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
        if not isinstance(payload, dict):
            continue
        if payload.get("direction") not in {"left", "right"}:
            continue

        event_id = str(payload.get("event_id") or "")
        user_id = str(payload.get("user_id") or "")
        event_timestamp = parse_datetime(payload.get("swiped_at"))
        if not event_id or not user_id or event_timestamp is None:
            continue

        snapshot = payload.get("event_snapshot") or {}
        catalog_event = events.get(event_id, {})
        segment = normalize_segment(snapshot.get("segmento") or catalog_event.get("segmento"))
        genre = normalize_genre(snapshot.get("genero") or catalog_event.get("genero"), segment)
        swipe = {
            "interaction_id": message_id or f"{user_id}:{event_id}:{event_timestamp.isoformat()}",
            "user_id": user_id,
            "event_id": event_id,
            "event_name": snapshot.get("nombre") or catalog_event.get("nombre"),
            "recinto_nombre": snapshot.get("recinto_nombre") or catalog_event.get("recinto_nombre"),
            "event_timestamp": event_timestamp,
            "liked": payload.get("direction") == "right",
            "dwell_ms": int(payload.get("dwell_ms") or 0),
            "recommendation_context": payload.get("recommendation_context") or "swipe",
            "segmento": segment,
            "genero": genre,
            "subgenero": snapshot.get("subgenero") or catalog_event.get("subgenero"),
            "ciudad": snapshot.get("ciudad") or catalog_event.get("ciudad"),
            "banda_precio": price_band(snapshot.get("banda_precio") or catalog_event.get("banda_precio")),
            "price_mid": price_mid({**catalog_event, **snapshot}),
            "fecha_evento": parse_date(snapshot.get("fecha_evento") or catalog_event.get("fecha")),
        }
        swipes.append(swipe)

    if not swipes:
        raise RuntimeError(f"No parseable swipe rows found in {SWIPES_RAW_PATH}")
    return swipes


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def reference_city(swipes: list[dict[str, Any]]) -> tuple[str, str, int, int]:
    counts: dict[str, dict[str, Any]] = {}
    for swipe in swipes:
        city = (swipe.get("ciudad") or "").strip()
        if not city:
            continue
        bucket = counts.setdefault(city, {"total": 0, "likes": 0, "latest": swipe["event_timestamp"]})
        bucket["total"] += 1
        bucket["likes"] += 1 if swipe["liked"] else 0
        bucket["latest"] = max(bucket["latest"], swipe["event_timestamp"])
    if not counts:
        return "", "", 0, 0
    city, data = sorted(
        counts.items(),
        key=lambda item: (
            item[1]["likes"] <= 0,
            -item[1]["likes"],
            -item[1]["total"],
            -item[1]["latest"].timestamp(),
            item[0],
        ),
    )[0]
    source = "liked_swipes_90d" if data["likes"] > 0 else "swipes_90d"
    return city, source, int(data["total"]), int(data["likes"])


def summarize_window(swipes: list[dict[str, Any]], days: int, ref_time: datetime) -> dict[str, Any]:
    window_swipes = [s for s in swipes if s["event_timestamp"] >= ref_time - timedelta(days=days)]
    liked_swipes = [s for s in window_swipes if s["liked"]]
    total = len(window_swipes)
    liked_total = len(liked_swipes)
    output: dict[str, Any] = {
        f"total_swipes_{days}d": total,
        f"total_right_swipes_{days}d": liked_total,
        f"right_swipe_rate_{days}d": ratio(liked_total, total),
        f"avg_dwell_ms_{days}d": average([float(s["dwell_ms"]) for s in window_swipes]),
        f"avg_right_dwell_ms_{days}d": average([float(s["dwell_ms"]) for s in liked_swipes]),
        f"distinct_segments_liked_{days}d": len({s["segmento"] for s in liked_swipes}),
        f"distinct_genres_liked_{days}d": len({s["genero"] for s in liked_swipes}),
        f"distinct_cities_liked_{days}d": len({s["ciudad"] for s in liked_swipes if s.get("ciudad")}),
        f"avg_days_until_event_liked_{days}d": average(
            [
                float((s["fecha_evento"] - s["event_timestamp"].date()).days)
                for s in liked_swipes
                if s.get("fecha_evento")
            ]
        ),
        f"avg_price_mid_liked_{days}d": average([float(s["price_mid"]) for s in liked_swipes]),
        f"median_price_mid_liked_{days}d": sorted([float(s["price_mid"]) for s in liked_swipes] or [0.0])[
            len(liked_swipes) // 2
        ],
        f"avg_price_mid_disliked_{days}d": average([float(s["price_mid"]) for s in window_swipes if not s["liked"]]),
        f"chat_swipe_share_{days}d": ratio(
            len([s for s in window_swipes if s["recommendation_context"] == "chat"]),
            total,
        ),
        f"chat_right_rate_{days}d": ratio(
            len([s for s in window_swipes if s["recommendation_context"] == "chat" and s["liked"]]),
            len([s for s in window_swipes if s["recommendation_context"] == "chat"]),
        ),
    }
    last_like = max((s["event_timestamp"] for s in liked_swipes), default=None)
    output[f"days_since_last_right_swipe_{days}d"] = (
        int((ref_time - last_like).days) if last_like else days + 7
    )

    for segment in SEGMENTS:
        total_segment = len([s for s in window_swipes if s["segmento"] == segment])
        liked_segment = len([s for s in liked_swipes if s["segmento"] == segment])
        key = segment.lower()
        output[f"like_rate_segment_{key}_{days}d"] = ratio(liked_segment, total_segment)
        output[f"swipe_share_segment_{key}_{days}d"] = ratio(total_segment, total)
        output[f"liked_share_segment_{key}_{days}d"] = ratio(liked_segment, liked_total)
        output[f"preference_lift_segment_{key}_{days}d"] = ratio(liked_segment, total_segment) - ratio(liked_total, total)

    for genre in GENRES:
        total_genre = len([s for s in window_swipes if s["genero"] == genre])
        liked_genre = len([s for s in liked_swipes if s["genero"] == genre])
        key = genre.lower()
        output[f"like_rate_genre_{key}_{days}d"] = ratio(liked_genre, total_genre)
        output[f"swipe_share_genre_{key}_{days}d"] = ratio(total_genre, total)
        output[f"liked_share_genre_{key}_{days}d"] = ratio(liked_genre, liked_total)
        output[f"preference_lift_genre_{key}_{days}d"] = ratio(liked_genre, total_genre) - ratio(liked_total, total)

    for band in PRICE_BANDS:
        total_band = len([s for s in window_swipes if s["banda_precio"] == band])
        liked_band = len([s for s in liked_swipes if s["banda_precio"] == band])
        key = {"bajo": "low", "medio": "medium", "alto": "high"}[band]
        output[f"like_rate_price_band_{key}_{days}d"] = ratio(liked_band, total_band)
        output[f"swipe_share_price_band_{key}_{days}d"] = ratio(total_band, total)
        output[f"liked_share_price_band_{key}_{days}d"] = ratio(liked_band, liked_total)
        output[f"preference_lift_price_band_{key}_{days}d"] = ratio(liked_band, total_band) - ratio(liked_total, total)
    return output


def build_feature_export(swipes: list[dict[str, Any]], destination: Path) -> list[dict[str, Any]]:
    ref_time = max(s["event_timestamp"] for s in swipes)
    swipes_by_user: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for swipe in swipes:
        swipes_by_user[swipe["user_id"]].append(swipe)

    rows = []
    for user_id, user_swipes in sorted(swipes_by_user.items()):
        city, city_source, city_swipes, city_likes = reference_city(user_swipes)
        row = {
            "user_id": user_id,
            "reference_city": city,
            "home_city": city,
            "reference_city_source": city_source,
            "reference_city_swipes_90d": city_swipes,
            "reference_city_likes_90d": city_likes,
        }
        for days in (30, 90):
            row.update(summarize_window(user_swipes, days, ref_time))
        row["right_swipe_rate_delta_30_vs_90"] = row["right_swipe_rate_30d"] - row["right_swipe_rate_90d"]
        row["total_swipes_delta_30_vs_90"] = row["total_swipes_30d"] - row["total_swipes_90d"]
        rows.append(row)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    return rows


def run_training(feature_csv: Path, training_dir: Path) -> None:
    command = [
        sys.executable,
        str(TRAINING_SCRIPT),
        "--input-csv",
        str(feature_csv),
        "--output-dir",
        str(training_dir),
        "--k-values",
        K_VALUES,
    ]
    log("running clustering training")
    subprocess.run(command, check=True)


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def taxonomy(event: dict[str, Any]) -> tuple[str, str, str]:
    segment = normalize_segment(event.get("segmento"))
    genre = normalize_genre(event.get("genero"), segment)
    return segment, genre, price_band(event.get("banda_precio"))


def event_display_key(event: dict[str, Any]) -> tuple[str, str, str]:
    return (
        str(event.get("nombre") or event.get("event_name") or "").strip().lower(),
        str(event.get("recinto_nombre") or "").strip().lower(),
        str(event.get("ciudad") or "").strip().lower(),
    )


def build_recommendations(
    swipes: list[dict[str, Any]],
    events: dict[str, dict[str, Any]],
    training_dir: Path,
    output_path: Path,
) -> list[dict[str, Any]]:
    assignments = load_csv(training_dir / "user_cluster_assignments.csv")
    assignments_by_user = {row["user_id"]: row for row in assignments}
    seen_by_user: dict[str, set[str]] = defaultdict(set)
    seen_display_keys_by_user: dict[str, set[tuple[str, str, str]]] = defaultdict(set)
    liked_taxonomy_by_user: dict[str, Counter[tuple[str, str, str]]] = defaultdict(Counter)
    cluster_taxonomy: dict[int, Counter[tuple[str, str, str]]] = defaultdict(Counter)

    for swipe in swipes:
        user_id = swipe["user_id"]
        seen_by_user[user_id].add(swipe["event_id"])
        seen_display_keys_by_user[user_id].add(
            (
                str(swipe.get("event_name") or "").strip().lower(),
                str(swipe.get("recinto_nombre") or "").strip().lower(),
                str(swipe.get("ciudad") or "").strip().lower(),
            )
        )
        if swipe["liked"]:
            key = (swipe["segmento"], swipe["genero"], swipe["banda_precio"])
            liked_taxonomy_by_user[user_id][key] += 1
            cluster_id = int(assignments_by_user[user_id]["cluster_id"])
            cluster_taxonomy[cluster_id][key] += 1

    recommendations = []
    today = max((s["event_timestamp"].date() for s in swipes), default=date.today())
    for user_id, assignment in assignments_by_user.items():
        cluster_id = int(assignment["cluster_id"])
        user_seen = seen_by_user[user_id]
        user_seen_display_keys = seen_display_keys_by_user[user_id]
        user_likes = liked_taxonomy_by_user[user_id]
        cluster_likes = cluster_taxonomy[cluster_id]
        scored = []
        scored_display_keys: set[tuple[str, str, str]] = set()
        for event in events.values():
            event_id = str(event.get("id") or event.get("event_id") or "")
            display_key = event_display_key(event)
            if not event_id or event_id in user_seen or display_key in user_seen_display_keys:
                continue
            if display_key in scored_display_keys:
                continue
            scored_display_keys.add(display_key)
            segment, genre, band = taxonomy(event)
            key = (segment, genre, band)
            event_date = parse_date(event.get("fecha"))
            days_until = (event_date - today).days if event_date else 30
            score = 0.10
            score += 0.45 * ratio(cluster_likes[key], sum(cluster_likes.values()))
            score += 0.30 * ratio(user_likes[key], sum(user_likes.values()))
            score += 0.10 if assignment.get("reference_city") and assignment.get("reference_city") == event.get("ciudad") else 0.0
            score += max(0.0, 0.05 - max(days_until, 0) * 0.002)
            scored.append(
                {
                    "user_id": user_id,
                    "event_id": event_id,
                    "event_name": event.get("nombre"),
                    "fecha_evento": event.get("fecha"),
                    "ciudad": event.get("ciudad"),
                    "recinto_nombre": event.get("recinto_nombre"),
                    "segmento": segment,
                    "genero": genre,
                    "subgenero": event.get("subgenero"),
                    "recommendation_score": round(score, 6),
                    "cluster_source": "own_cluster",
                }
            )

        if not scored:
            raise RuntimeError(f"No recommendation candidates left for user {user_id}; add more seed events or swipe fewer cards.")

        scored.sort(key=lambda row: (-float(row["recommendation_score"]), row.get("fecha_evento") or "", row["event_id"]))
        for rank, row in enumerate(scored[:MAX_RECOMMENDATIONS], start=1):
            row["recommendation_rank"] = rank
            recommendations.append(row)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_RECOMMENDATION_FIELDS)
        writer.writeheader()
        for row in recommendations:
            writer.writerow({field: row.get(field, "") for field in CSV_RECOMMENDATION_FIELDS})
    return recommendations


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    feature_csv = OUTPUT_DIR / "dim_user_cluster_features_current.csv"
    training_dir = OUTPUT_DIR / "training_outputs"

    events = load_events()
    swipes = load_swipes(events)
    features = build_feature_export(swipes, feature_csv)
    if not features or not feature_csv.exists():
        raise RuntimeError("Feature export was not generated.")

    run_training(feature_csv, training_dir)
    if not (training_dir / "user_cluster_assignments.csv").exists():
        raise RuntimeError("Training did not produce user_cluster_assignments.csv.")

    recommendations = build_recommendations(swipes, events, training_dir, RECOMMENDATIONS_OUTPUT_PATH)
    if not recommendations:
        raise RuntimeError("No local recommendations were generated.")

    log(f"swipes parsed: {len(swipes)}")
    log(f"feature users: {len(features)}")
    log(f"recommendations: {len(recommendations)}")
    log(f"backend fallback CSV: {RECOMMENDATIONS_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
